"""Node Design — Technical Designer: tạo Design Document từ PRD."""
import os
from pathlib import Path
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig

from graph.state import (
    SoftwareFactoryState,
    count_rejects,
    update_node_stats,
    push_content_history,
)
from graph.llm import llm_factory
from graph.repo_store import (
    save_design, read_design, save_prd, read_prd, read_gate_feedback,
    read_ux_spec, AGENT_WORKSPACE_ROOT,
)
from graph.prompt_loader import load_prompt


def _design_node_simple(
    state: SoftwareFactoryState, thread_id: str, prd: str, feedback_history: str,
    ux_spec: str = "",
) -> Dict[str, Any]:
    """Cách cũ: 1 lệnh gọi LLM, không tool, không kế hoạch."""
    provider_name = os.getenv("DESIGN_PROVIDER", None)
    llm = llm_factory(provider_name)

    system_prompt = load_prompt("design_system")
    user_prompt = f"## PRD ĐÃ DUYỆT\n\n{prd}\n\n"
    if ux_spec:
        user_prompt += f"## UX SPEC (từ Sally, UX Designer — BẮT BUỘC dùng lại danh sách màn hình)\n\n{ux_spec}\n\n"
    if feedback_history:
        user_prompt += (
            f"## LỊCH SỬ NHẬN XÉT TỪ REVIEWER\n"
            + feedback_history
            + "\nLưu ý các nhận xét trên khi cập nhật tài liệu thiết kế.\n\n"
            f"Hãy cập nhật lại design document theo nhận xét trên."
        )
    else:
        user_prompt += "Hãy viết Design Document chi tiết dựa trên PRD trên."

    llm_response = llm.call(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=20000,
    )
    result = llm_response.content

    if result is None:
        return {
            "design_doc": "## LỖI: LLM không trả về Design Document.",
            "status": "failed",
            "error": "LLM returned None",
        }

    save_design(thread_id, result)

    # ── Observability: token/model/history ──
    # gate_design đứng ngay sau "design" trong graph (design -> gate_design).
    node_stats = update_node_stats(
        state.node_stats, "design",
        reject_count=count_rejects(state.gate_history, "gate_design"),
        tokens_used=llm_response.total_tokens,
        model=llm_response.model,
    )
    content_history = push_content_history(state.content_history, "design", result)

    return {
        "design_doc": result,
        "status": "running",
        "gate_decision": None,
        "current_gate": "",
        "pending_gate_role": "",
        "node_stats": node_stats,
        "content_history": content_history,
    }


def _design_node_agentic(
    state: SoftwareFactoryState, thread_id: str, prd: str, feedback_history: str,
    ux_spec: str = "",
) -> Dict[str, Any]:
    """Cách mới: dùng OpenCode agent (opencode serve HTTP REST) — agent tự đọc file,
    lập kế hoạch, viết DESIGN.md, tự kiểm tra và tự sửa.
    """
    from graph.agent_runtime import run_agent

    # Workspace trong AGENT_WORKSPACE_ROOT/<threadID>/design_work
    workspace_path = AGENT_WORKSPACE_ROOT / thread_id / "design_work"

    design_prompt_content = load_prompt("design_system")

    prev_design_block = ""
    if feedback_history:
        prev_design = read_design(thread_id)
        if prev_design:
            prev_design_block = (
                f"\n## BẢN DESIGN TRƯỚC (đã bị từ chối, PHẢI đọc kỹ và SỬA TRÊN BẢN NÀY,\n"
                f"KHÔNG viết lại từ đầu — chỉ sửa đúng phần bị phản hồi):\n\n{prev_design}\n"
            )

    feedback_block = (
        f'\n## PHẢN HỒI TỪ BẢN DUYỆT TRƯỚC (bắt buộc phải xử lý):\n"{feedback_history}"\n'
        if feedback_history else ""
    )

    ux_block = (
        f"\n## UX SPEC (từ Sally, UX Designer — BẮT BUỘC dùng lại danh sách màn hình)\n{ux_spec}\n"
        if ux_spec else ""
    )

    instructions = f"""Read the PRD below and write a Design Document into file DESIGN.md.

## PRD ĐÃ DUYỆT
{prd}
{ux_block}{feedback_block}{prev_design_block}
Quy ước cấu trúc Design Document (BẮT BUỘC tuân theo):
{design_prompt_content}

Quy trình làm việc:
1. {"Đọc bản DESIGN cũ ở trên, xác định đúng phần cần sửa theo phản hồi, sửa TRÊN BẢN ĐÓ." if feedback_history else "Viết DESIGN.md hoàn chỉnh theo đúng cấu trúc quy định."}
2. Đọc lại DESIGN.md vừa viết/sửa, tự kiểm tra: có thiếu yêu cầu nào từ PRD gốc
   không, có mâu thuẫn nội bộ không. Sửa lại nếu cần.
3. Khi thực sự hoàn tất, dừng lại.
"""

    cfg = {
        "model": os.getenv("DESIGN_LLM_MODEL", os.getenv("NVIDIA_MODEL", "openai/gpt-oss-120b")),
        "api_key": os.getenv("DESIGN_LLM_API_KEY", os.getenv("NVIDIA_API_KEY", "")),
        "base_url": os.getenv("DESIGN_LLM_BASE_URL", os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")),
    }

    result = run_agent(
        "opencode",
        {"instructions": instructions, "workspace_path": workspace_path, "output_file": "DESIGN.md"},
        cfg,
    )

    if result["status"] != "completed":
        return {
            "design_doc": f"## LỖI: Agent thất bại — {result['log']}",
            "status": "failed",
            "error": result["log"],
        }

    design_doc = result["output"]
    save_design(thread_id, design_doc)

    node_stats = update_node_stats(
        state.node_stats, "design",
        reject_count=count_rejects(state.gate_history, "gate_design"),
        tokens_used=result["prompt_tokens"] + result["completion_tokens"],
        model=result["model"],
    )
    content_history = push_content_history(state.content_history, "design", design_doc)

    return {
        "design_doc": design_doc,
        "status": "running",
        "gate_decision": None,
        "current_gate": "",
        "pending_gate_role": "",
        "node_stats": node_stats,
        "content_history": content_history,
    }


def _design_node_bmad(
    state: SoftwareFactoryState, thread_id: str, prd: str, feedback_history: str,
    ux_spec: str = "",
) -> Dict[str, Any]:
    """Gọi skill `bmad-architecture` THẬT qua OpenCode headless. Khác
    `bmad-prd`: schema trả về field `spine` (ARCHITECTURE-SPINE.md), không
    phải `design`; input còn yêu cầu thêm `altitude`/`purpose` (đã verify
    trong headless.md của chính skill này). Bật qua DESIGN_USE_BMAD_SKILL=true.

    altitude="feature" là giá trị TĨNH theo đúng thiết kế đã thống nhất
    trước đây (meeting.py cũng dùng cùng giá trị mặc định này) — chưa có cơ
    chế tự chấm altitude theo nội dung thực tế.
    """
    from graph.bmad_headless import (
        ensure_bmad_installed, build_real_headless_prompt, parse_generic_json_tail,
    )

    workspace_path = AGENT_WORKSPACE_ROOT / thread_id / "design_work_bmad"
    workspace_path.mkdir(parents=True, exist_ok=True)

    ok, msg = ensure_bmad_installed(workspace_path, tools="opencode")
    if not ok:
        return {
            "design_doc": f"## LỖI: không cài được _bmad/ ({msg}) — dùng DESIGN_USE_AGENT=true để fallback nhánh agentic custom-prompt.",
            "status": "failed",
            "error": msg,
        }

    common_header = (
        "- altitude: feature\n"
        "- purpose: build-substrate\n"
    )

    if feedback_history:
        intent_type = "update"
        payload_lines = (
            common_header +
            "- ARCHITECTURE-SPINE.md đã tồn tại trong workspace hiện tại (nếu "
            "chưa từng chạy create trước đó ở workspace này, coi đây là "
            "create thay vì update)\n"
            f"- change signal (điều cần sửa và lý do):\n{feedback_history}\n"
        )
    else:
        intent_type = "create"
        payload_lines = common_header + f"- driving input (PRD đã duyệt):\n{prd}\n"
        if ux_spec:
            payload_lines += f"- UX Spec (BẮT BUỘC dùng lại danh sách màn hình):\n{ux_spec}\n"

    instructions = build_real_headless_prompt(
        skill_name="bmad-architecture",
        intent_type=intent_type,
        payload_lines=payload_lines,
    )

    cfg = {
        "model": os.getenv("DESIGN_LLM_MODEL", os.getenv("NVIDIA_MODEL", "openai/gpt-oss-120b")),
        "api_key": os.getenv("DESIGN_LLM_API_KEY", os.getenv("NVIDIA_API_KEY", "")),
        "base_url": os.getenv("DESIGN_LLM_BASE_URL", os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")),
    }

    result = run_agent(
        "opencode",
        {"instructions": instructions, "workspace_path": workspace_path, "output_file": None},
        cfg,
    )

    if result["status"] != "completed":
        return {
            "design_doc": f"## LỖI: bmad-architecture headless thất bại — {result['log']}",
            "status": "failed",
            "error": result["log"],
        }

    headless = parse_generic_json_tail(result.get("output", ""))

    design_doc = ""
    spine_path_str = headless.get("spine")
    if spine_path_str:
        spine_path = Path(spine_path_str)
        if not spine_path.is_absolute():
            spine_path = workspace_path / spine_path_str
        if spine_path.exists():
            design_doc = spine_path.read_text(encoding="utf-8")

    if not design_doc:
        candidates = list(workspace_path.rglob("ARCHITECTURE-SPINE.md"))
        if candidates:
            design_doc = candidates[0].read_text(encoding="utf-8")

    if not design_doc:
        return {
            "design_doc": (
                f"## LỖI: bmad-architecture headless không tạo được spine đọc "
                f"được (status={headless.get('status', 'unknown')}).\nRaw "
                f"output (500 ký tự cuối): {result.get('output', '')[-500:]}"
            ),
            "status": "failed",
            "error": "ARCHITECTURE-SPINE.md not found after bmad-architecture headless run",
        }

    save_design(thread_id, design_doc)

    pipeline_status = "running" if headless.get("status") == "complete" else "failed"

    node_stats = update_node_stats(
        state.node_stats, "design",
        reject_count=count_rejects(state.gate_history, "gate_design"),
        tokens_used=result["prompt_tokens"] + result["completion_tokens"],
        model=result["model"],
    )
    content_history = push_content_history(state.content_history, "design", design_doc)

    updates: Dict[str, Any] = {
        "design_doc": design_doc,
        "status": pipeline_status,
        "gate_decision": None,
        "current_gate": "",
        "pending_gate_role": "",
        "node_stats": node_stats,
        "content_history": content_history,
    }

    open_questions = headless.get("open_questions") or []
    if open_questions:
        updates["pending_escalation_questions"] = "\n".join(f"- {q}" for q in open_questions)

    return updates


def design_node(state: SoftwareFactoryState, config: RunnableConfig | None = None) -> Dict[str, Any]:
    """Chuyển prd_approved/prd_v1 → design_doc.

    Bật/tắt nhánh agentic (OpenCode) qua biến môi trường DESIGN_USE_AGENT=true —
    mặc định TẮT (dùng cách cũ) để không phá vỡ hành vi hiện tại.
    
    Args:
        state: SoftwareFactoryState hiện tại
        config: LangGraph configurable chứa thread_id (được inject tự động)
    
    Returns a dict with:
        - design_doc (Markdown)
        - status (running/failed)
        - error (optional)
    """
    # Lấy thread_id từ config (LangGraph inject khi hàm có parameter config)
    thread_id = "default"
    if config:
        configurable = config.get("configurable", {}) or {}
        thread_id = configurable.get("thread_id", "default")
    
    prd = state.prd_approved.strip() or state.prd_v1.strip()
    if not prd:
        prd = read_prd(thread_id)
    
    if not prd:
        return {
            "design_doc": "## LỖI: Không có PRD được duyệt để tạo Design. Vui lòng chạy PRD node trước.",
            "status": "failed",
            "error": "prd_v1 and prd_approved are empty",
        }
    
    feedback_history = read_gate_feedback(thread_id, "gate_design")
    readiness_feedback = read_gate_feedback(thread_id, "gate_readiness")
    if readiness_feedback:
        feedback_history = (
            f"{feedback_history}\n\n[Từ gate_readiness — phát hiện lệch cross-artifact]\n{readiness_feedback}"
            if feedback_history else f"[Từ gate_readiness — phát hiện lệch cross-artifact]\n{readiness_feedback}"
        )
    critic_feedback = state.upstream_feedback.get("design", "")
    if critic_feedback:
        feedback_history = (
            f"{feedback_history}\n\n[Từ critic pass]\n{critic_feedback}"
            if feedback_history else critic_feedback
        )

    ux_spec = state.ux_spec.strip()
    if not ux_spec:
        ux_spec = read_ux_spec(thread_id)

    use_bmad_skill = os.getenv("DESIGN_USE_BMAD_SKILL", "false").strip().lower() in ("1", "true", "yes")
    if use_bmad_skill:
        return _design_node_bmad(state, thread_id, prd, feedback_history, ux_spec)

    use_agent = os.getenv("DESIGN_USE_AGENT", "false").strip().lower() in ("1", "true", "yes")
    if use_agent:
        return _design_node_agentic(state, thread_id, prd, feedback_history, ux_spec)
    return _design_node_simple(state, thread_id, prd, feedback_history, ux_spec)

# Alias để GraphBuilder dùng
DESIGN_NODE = design_node