"""BA Node — phân tích yêu cầu + sinh PRD Draft."""

from langchain_core.runnables import RunnableConfig

from graph.llm import llm_factory
from graph.state import SoftwareFactoryState, MAX_HISTORY_VERSIONS


# Mapping node_name → gate_name để tính reject_count (None = không có gate ngay sau ba)
_NODE_GATES = {
    "ba": None,       # Ba không có gate ngay sau nó
    "prd": "gate_prd",
    "design": "gate_design",
    "ui": "gate_mockup",
}


def ba_node(state: SoftwareFactoryState, config: RunnableConfig | None = None):
    """Node phân tích nghiệp vụ: nhận raw_requirements → sinh prd_draft."""
    print("[BA Node] 📝 Phân tích yêu cầu...")

    state, updates = _ba_node_logic(state)
    return updates


def _ba_node_logic(state: SoftwareFactoryState):
    """Logic chính của BA Node — trả về (state, updates)."""
    from graph.stats_utils import count_rejects

    updates = {}

    # Lấy nội dung yêu cầu
    requirements = state.raw_requirements or ""

    # Prompt chi tiết cho BA
    system_prompt = "Bạn là Business Analyst chuyên nghiệp. Phân tích yêu cầu và tạo PRD dự thảo."
    user_prompt = f"""Phân tích yêu cầu sau và tạo PRD dự thảo:

Yêu cầu:
{requirements}

Hãy đảm bảo PRD bao gồm:
1. Mô tả tổng quan sản phẩm
2. Các stakeholders và personas
3. Use cases và user stories
4. Requirements (functional và non-functional)
5. Acceptance criteria
6. Timeline và milestones
"""

    # Gọi LLM
    llm = llm_factory("nvidia")
    llm_response = llm.call(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
    )
    result = llm_response.content or ""

    # Cập nhật prd_draft
    updates["prd_draft"] = result

    # --- Cập nhật node_stats ---
    node_name = "ba"
    gate_name = _NODE_GATES.get(node_name)
    reject_count = count_rejects(state.gate_history, gate_name) if gate_name else 0

    stats = dict(state.node_stats)
    existing = stats.get(node_name, {})
    stats[node_name] = {
        "reject_count": reject_count,
        "tokens_used": existing.get("tokens_used", 0) + llm_response.total_tokens,
        "model": llm_response.model,
    }
    updates["node_stats"] = stats

    # --- Cập nhật content_history ---
    all_history = dict(state.content_history)
    history = list(all_history.get(node_name, []))
    from datetime import datetime
    history.insert(0, {"content": result, "timestamp": datetime.now().isoformat()})
    history = history[:MAX_HISTORY_VERSIONS]
    all_history[node_name] = history
    updates["content_history"] = all_history

    print(f"[BA Node] ✅ Đã tạo PRD dự thảo ({len(result)} chars)")
    return state, updates


# Alias để GraphBuilder dùng
BA_NODE = ba_node
