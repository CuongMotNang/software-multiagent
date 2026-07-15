"""Graph Builder for SoftwareFactory pipeline.

This module builds a LangGraph **StateGraph** that wires together the three
nodes that have already been implemented:

* ``ba_node``     – Business Analyst (raw_requirements -> prd_draft)
* ``prd_node``    – Product Manager (prd_draft -> prd_v1)
* ``design_node`` – Technical Designer (prd_v1 -> design_doc)

The graph uses **PostgresSaver** (langgraph-checkpoint-postgres) for durable
checkpointing. If ``DATABASE_URL`` is missing, or the psycopg backend cannot
be loaded (e.g. libpq / binary wheel missing on the host), the builder falls
back to ``InMemorySaver`` so the pipeline can still be exercised locally.

Key points that match the ACTUAL LangGraph Python implementation:

* The underlying Postgres schema consists of four fixed tables:
  ``checkpoints``, ``checkpoint_blobs``, ``checkpoint_writes``, and
  ``checkpoint_migrations``. We do **not** rename these tables.
* Each checkpoint is identified by the **composite** primary key
  ``(thread_id, checkpoint_ns, checkpoint_id)`` -- there is no auto-increment
  ``id`` column.
* The **state values** are stored in ``checkpoint_blobs`` as ``BYTEA`` per
  channel; the ``checkpoints`` table only holds metadata (version, ts, ...).
* A **thread_id** must be supplied (via ``config``) for resume capability.
* The saver **must be set up** (``saver.setup()``) before first use --
  this is idempotent, safe to call on every process start.
* Execution is performed with ``graph.invoke(state, config)`` (or
  ``graph.stream(state, config)`` for streaming). ``invoke`` returns a
  SINGLE value (the final state), not a tuple.

IMPORTANT -- Python-specific (this is where earlier drafts got it wrong):

* ``PostgresSaver`` in the Python package has **no** ``.from_url()``
  classmethod and **no** ``schema=`` keyword. Those only exist in the
  JavaScript/TypeScript package. The real constructors are
  ``PostgresSaver.from_conn_string(uri)`` (returns a context manager) or
  ``PostgresSaver(connection_or_pool)`` (works with a plain connection OR a
  ``psycopg_pool.ConnectionPool`` -- the latter is what we use below so the
  connection survives across calls instead of being closed when a ``with``
  block exits).
* Custom Postgres *schema* (namespace) is **not** configurable in the
  Python package -- tables always live in the default ``public`` schema.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

# Local imports -- the nodes and the shared state model
from graph.state import SoftwareFactoryState
from graph.nodes.ba_node import BA_NODE
from graph.nodes.debate_prd import DEBATE_PRD, should_debate_prd
from graph.nodes.prd_node import PRD_NODE
from graph.nodes.critic_prd import CRITIC_PRD
from graph.nodes.design_node import DESIGN_NODE
from graph.nodes.design_tokens_node import DESIGN_TOKENS_NODE
from graph.nodes.gate_prd import GATE_PRD
from graph.nodes.gate_design import GATE_DESIGN
from graph.nodes.ui_node import UI_NODE
from graph.nodes.gate_mockup import GATE_MOCKUP
from graph.nodes.engineer_node import ENGINEER_NODE
from graph.repo_store import save_manifest, list_artifacts

# Module-level cache: ONE connection pool for the whole process.
# Re-creating a pool on every get_checkpointer() call would leak connections.
_pool = None


def _load_env() -> None:
    """Load ``.env`` from the project root if it exists.

    The ``.env`` file lives one level above the ``softwarefactory`` package
    (i.e. ``../.env`` relative to this file). ``python-dotenv`` silently
    ignores a missing file, which is fine for the pure in-memory fallback.
    """
    env_path = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(env_path)


def get_checkpointer() -> Any:
    """Return a checkpoint saver.

    * If ``DATABASE_URL`` is set AND the psycopg backend loads correctly,
      we use ``PostgresSaver`` backed by a shared ``ConnectionPool``.
    * Otherwise we fall back to ``InMemorySaver`` (RAM only, lost on
      restart) -- useful for quick local tests or environments where the
      Postgres driver isn't installed yet.

    The saver is set up (tables created) before being returned.
    """
    global _pool

    _load_env()
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        return InMemorySaver()

    try:
        from psycopg_pool import ConnectionPool
        from psycopg.rows import dict_row
        from langgraph.checkpoint.postgres import PostgresSaver
    except Exception as import_err:  # pragma: no cover -- env-dependent
        print(
            f"[graph_builder] WARNING: Postgres backend unavailable "
            f"({import_err}). Falling back to InMemorySaver.\n"
            f"  Fix with: pip install \"psycopg[binary,pool]\""
        )
        return InMemorySaver()

    if _pool is None:
        _pool = ConnectionPool(
            conninfo=db_url,
            max_size=10,
            kwargs={"autocommit": True, "row_factory": dict_row},
        )

    saver = PostgresSaver(_pool)
    saver.setup()  # idempotent -- creates the 4 tables only if missing
    return saver


# "approve_with_edit" = BA/Dev tự sửa tay (vd: Puck editor ở gate_mockup)
# rồi bấm approve — về mặt luồng phải xử lý y hệt "approve" (đi tiếp).
# Trước đây các hàm route dưới đây chỉ so khớp đúng "approve", nên
# "approve_with_edit" bị rơi vào nhánh default và bị coi như reject —
# đây là bug, không phải hành vi cố ý.
_APPROVE_DECISIONS = ("approve", "approve_with_edit")


def route_critic_prd(state: SoftwareFactoryState) -> str:
    """Quyết định sau critic pass ở bước PRD (xem graph/triage.py).

    - loop_upstream (bad_spec) -> quay lại "ba" thật sự (KHÔNG phải tự-loop
      trong "prd" như route_gate_prd cũ vẫn làm với reject/edit).
    - auto_patch -> quay lại "prd" để tự sửa tại chỗ.
    - proceed / halt_escalate -> luôn đi tiếp "gate_prd". halt_escalate
      KHÔNG bỏ qua gate — chỉ mang theo pending_escalation_questions để
      gate_prd hiển thị cho người quyết định, gate người vẫn luôn xảy ra.
    """
    action = state.get("triage_action", {}).get("prd") if isinstance(state, dict) \
        else state.triage_action.get("prd")
    if action == "loop_upstream":
        return "ba"
    if action == "auto_patch":
        return "prd"
    return "gate_prd"


def route_after_ba(state: SoftwareFactoryState) -> str:
    """Quyết định sau 'ba': vào phòng họp debate_prd trước, hay đi thẳng 'prd'.

    Dùng graph.nodes.debate_prd.should_debate_prd() — hiện tại static (altitude/
    criticality_high chưa có nguồn dữ liệu thật trong state, đã thống nhất để
    tĩnh, không chặn việc build). Vì "prd" được đánh dấu evaluation-like=True
    trong meeting._EVALUATION_LIKE_NODES nên hàm này luôn trả "debate_prd".
    """
    return "debate_prd" if should_debate_prd() else "prd"


def route_gate_prd(state: SoftwareFactoryState) -> str:
    """Quyết định chuyển tiếp sau khi BA duyệt PRD.

    Approve (kể cả approve_with_edit) → tiếp tục sang design.
    Reject/Edit → lặp lại prd (không chạy lại ba).
    """
    decision = state.get("gate_decision") if isinstance(state, dict) else state.gate_decision
    if decision in _APPROVE_DECISIONS:
        return "design"
    elif decision in ["edit", "reject"]:
        return "prd"
    return "prd"


def route_gate_design(state: SoftwareFactoryState) -> str:
    """Quyết định chuyển tiếp sau khi Dev duyệt Design Doc.

    Approve (kể cả approve_with_edit) → design_tokens (sinh design_tokens.json
    TRƯỚC khi vào ui — Giai đoạn 3.1, để ui_node luôn có tokens sẵn khi sinh screen).
    """
    decision = state.get("gate_decision") if isinstance(state, dict) else state.gate_decision
    if decision in _APPROVE_DECISIONS:
        return "design_tokens"
    elif decision in ["edit", "reject"]:
        return "design"
    return "design"


def route_gate_mockup(state: SoftwareFactoryState) -> str:
    """Quyết định chuyển tiếp sau khi BA duyệt Mockup UI.

    Approve (kể cả approve_with_edit — sửa tay qua Puck rồi bấm duyệt)
    → đi tiếp sang engineer.
    """
    decision = state.get("gate_decision") if isinstance(state, dict) else state.gate_decision
    if decision in _APPROVE_DECISIONS:
        return "engineer"
    elif decision in ["edit", "reject"]:
        return "ui"
    return "ui"


def build_graph(checkpointer: Any | None = None) -> Any:
    """Construct and compile the LangGraph pipeline.

    Parameters
    ----------
    checkpointer: optional
        An already-initialised checkpoint saver. If ``None`` the function
        calls :func:`get_checkpointer`.

    Returns
    -------
    A compiled ``CompiledStateGraph`` ready for ``invoke``/``stream``.
    """
    if checkpointer is None:
        checkpointer = get_checkpointer()
    # langgraph dev truyền checkpointer là dict config (từ langgraph.json)
    # LangGraph v1.2.6 không chấp nhận dict — chỉ chấp nhận BaseCheckpointSaver/True/False/None
    if isinstance(checkpointer, dict):
        checkpointer = None  # dùng checkpointer mặc định của runtime

    builder = StateGraph(SoftwareFactoryState)

    # Register nodes
    builder.add_node("ba", BA_NODE)          # raw_requirements -> prd_draft
    builder.add_node("debate_prd", DEBATE_PRD)  # prd_draft -> debate_synthesis["prd"]
    builder.add_node("prd", PRD_NODE)        # prd_draft (+debate_synthesis) -> prd_v1
    builder.add_node("critic_prd", CRITIC_PRD)  # prd_v1 -> critic pass + triage
    builder.add_node("design", DESIGN_NODE)  # prd_v1 -> design_doc
    builder.add_node("design_tokens", DESIGN_TOKENS_NODE)  # design_doc -> design_tokens.json (Giai đoạn 3.1)
    builder.add_node("gate_prd", GATE_PRD)   # BA reviews PRD
    builder.add_node("gate_design", GATE_DESIGN)  # Dev reviews Design Doc
    builder.add_node("ui", UI_NODE)          # UI Prototyper
    builder.add_node("gate_mockup", GATE_MOCKUP)  # BA reviews Mockup HTML
    builder.add_node("engineer", ENGINEER_NODE)   # Code generation via OpenHands

    # Workflow edges
    builder.add_edge(START, "ba")

    builder.add_conditional_edges(
        "ba",
        route_after_ba,
        {
            "debate_prd": "debate_prd",
            "prd": "prd",
        }
    )
    builder.add_edge("debate_prd", "prd")

    builder.add_edge("prd", "critic_prd")

    builder.add_conditional_edges(
        "critic_prd",
        route_critic_prd,
        {
            "ba": "ba",
            "prd": "prd",
            "gate_prd": "gate_prd",
        }
    )

    builder.add_conditional_edges(
        "gate_prd",
        route_gate_prd,
        {
            "design": "design",
            "prd": "prd"
        }
    )

    builder.add_edge("design", "gate_design")

    builder.add_conditional_edges(
        "gate_design",
        route_gate_design,
        {
            "design_tokens": "design_tokens",
            "design": "design"
        }
    )

    builder.add_edge("design_tokens", "ui")

    builder.add_edge("ui", "gate_mockup")

    builder.add_conditional_edges(
        "gate_mockup",
        route_gate_mockup,
        {
            "engineer": "engineer",
            "ui": "ui"
        }
    )

    builder.add_edge("engineer", END)

    return builder.compile(checkpointer=checkpointer)


# ---------------------------------------------------------------------------
# Helper utilities -- useful for external scripts or tests
# ---------------------------------------------------------------------------
def new_thread_id() -> str:
    """Generate a fresh UUID-4 string to be used as ``thread_id``.

    The SAME ``thread_id`` must be supplied in ``config`` for every
    ``graph.invoke``/``graph.stream`` call that should share checkpoint
    history (i.e. to resume a paused/interrupted run).
    """
    return str(uuid.uuid4())


if __name__ == "__main__":
    # Simple sanity-check when the module is executed directly.
    g = build_graph()
    print("Graph compiled successfully. Nodes:", list(g.get_graph().nodes))