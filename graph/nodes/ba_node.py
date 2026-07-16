"""Node BA — Business Analyst: phân tích yêu cầu thô → PRD draft."""
import os
from pathlib import Path
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from graph.state import (
    SoftwareFactoryState,
    update_node_stats,
    push_content_history,
)
from graph.llm import llm_factory
from graph.repo_store import save_prd, read_prd
from graph.prompt_loader import load_prompt


def _get_feedback(state: SoftwareFactoryState) -> str:
    """Lấy phản hồi chỉnh sửa gần nhất cho BA.

    Có 2 nguồn, gộp lại nếu cả hai đều có:
    1. gate_history của gate_prd — người bấm edit/reject trực tiếp ở gate.
    2. upstream_feedback['ba'] — critic_prd phát hiện bad_spec (PRD lệch so
       với bản phân tích BA gốc) và tự động quay lại BA, KHÔNG cần người
       phải bấm reject thủ công. Đây là backward-loop thật (khác node prd
       tự-loop), nên phải đọc riêng, không chỉ dựa vào gate_history.
    """
    parts = []

    if state.gate_history:
        prd_gates = [h for h in state.gate_history if h.get("gate") == "gate_prd"]
        if prd_gates:
            last_gate = prd_gates[-1]
            if last_gate.get("decision") in ["edit", "reject"]:
                note = last_gate.get("note", "")
                if note:
                    parts.append(f"[Từ người duyệt gate_prd]\n{note}")

    critic_fb = state.upstream_feedback.get("ba", "")
    if critic_fb:
        parts.append(f"[Từ critic pass ở bước PRD]\n{critic_fb}")

    return "\n\n".join(parts)


def _ba_node_simple(state: SoftwareFactoryState, thread_id: str, raw_req: str, feedback: str, debate_synthesis: str = "") -> Dict[str, Any]:
    """Cách cũ: 1 lệnh gọi LLM, không tool, không kế hoạch. Đây là baseline để A/B
    so sánh với nhánh agentic — KHÔNG xoá, giữ nguyên để dễ rollback."""
    provider_name = os.getenv("BA_PROVIDER") or None
    llm = llm_factory(provider_name)

    system_prompt = load_prompt("ba_system")
    user_prompt = f"## YÊU CẦU KHÁCH HÀNG\n\n{raw_req}\n\n"
    if debate_synthesis:
        user_prompt += (
            f"## KẾT LUẬN BUỔI HỌP TRƯỚC KHI PHÂN TÍCH (debate room)\n"
            f"{debate_synthesis}\n\n"
        )
    if feedback:
        user_prompt += (
            f"## PHẢN HỒI YÊU CẦU CHỈNH SỬA TỪ BẢN DUYỆT TRƯỚC\n"
            f"Người duyệt đã yêu cầu chỉnh sửa với ý kiến sau:\n"
            f"\"{feedback}\"\n\n"
            f"Hãy cập nhật lại bản phân tích yêu cầu (prd_draft) để đáp ứng phản hồi trên."
        )
    else:
        user_prompt += f"Hãy phân tích yêu cầu trên theo đúng cấu trúc đã quy định."

    llm_response = llm.call(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=20000,
    )
    result = llm_response.content

    if result is None:
        return {
            "prd_draft": "## LỖI: LLM không trả về kết quả. Vui lòng thử lại.",
            "status": "failed",
            "error": "LLM returned None",
        }

    save_prd(thread_id, result)
    node_stats = update_node_stats(
        state.node_stats, "ba",
        reject_count=0,
        tokens_used=llm_response.total_tokens,
        model=llm_response.model,
    )
    content_history = push_content_history(state.content_history, "ba", result)

    return {
        "prd_draft": result,
        "status": "running",
        "gate_decision": None,
        "current_gate": "",
        "node_stats": node_stats,
        "content_history": content_history,
    }


def _ba_node_agentic(state: SoftwareFactoryState, thread_id: str, raw_req: str, feedback: str, debate_synthesis: str = "") -> Dict[str, Any]:
    """Cách mới: dùng OpenCode agent (opencode serve HTTP REST) — đơn giản, đã test
    thành công trong test_opencode_simple.py. Agent tự đọc file, lập kế hoạch, viết
    PRD.md, tự kiểm tra và tự sửa.
    """
    from graph.agent_runtime import run_agent
    from graph.repo_store import AGENT_WORKSPACE_ROOT

    # Workspace trong AGENT_WORKSPACE_ROOT/<threadID>/ba_work
    workspace_path = AGENT_WORKSPACE_ROOT / thread_id / "ba_work"

    # Load prompt từ prompts/system/ba_system.txt
    ba_prompt_content = load_prompt("ba_system")

    prev_prd_block = ""
    if feedback:
        prev_prd = read_prd(thread_id)
        if prev_prd:
            prev_prd_block = (
                f"\n## BẢN PRD TRƯỚC (đã bị từ chối, PHẢI đọc kỹ và SỬA TRÊN BẢN NÀY,\n"
                f"KHÔNG viết lại từ đầu — chỉ sửa đúng phần bị phản hồi):\n\n{prev_prd}\n"
            )

    feedback_block = (
        f'\n## PHẢN HỒI TỪ BẢN DUYỆT TRƯỚC (bắt buộc phải xử lý):\n"{feedback}"\n'
        if feedback else ""
    )

    debate_block = (
        f"\n## KẾT LUẬN BUỔI HỌP TRƯỚC KHI PHÂN TÍCH (debate room)\n{debate_synthesis}\n"
        if debate_synthesis else ""
    )

    instructions = f"""Read the customer requirements below and write a PRD into file PRD.md.

## YÊU CẦU KHÁCH HÀNG
{raw_req}
{debate_block}{feedback_block}{prev_prd_block}
Quy ước cấu trúc PRD (BẮT BUỘC tuân theo):
{ba_prompt_content}

Quy trình làm việc:
1. {"Đọc bản PRD cũ ở trên, xác định đúng phần cần sửa theo phản hồi, sửa TRÊN BẢN ĐÓ." if feedback else "Viết PRD.md hoàn chỉnh theo đúng cấu trúc quy định."}
2. Đọc lại PRD.md vừa viết/sửa, tự kiểm tra: có thiếu yêu cầu nào từ đề bài gốc
   không, có mâu thuẫn nội bộ không. Sửa lại nếu cần.
3. Khi thực sự hoàn tất, dừng lại.
"""

    cfg = {
        "model": os.getenv("BA_LLM_MODEL", os.getenv("NVIDIA_MODEL", "openai/gpt-oss-120b")),
        "api_key": os.getenv("BA_LLM_API_KEY", os.getenv("NVIDIA_API_KEY", "")),
        "base_url": os.getenv("BA_LLM_BASE_URL", os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")),
    }

    result = run_agent(
        "opencode",
        {"instructions": instructions, "workspace_path": workspace_path, "output_file": "PRD.md"},
        cfg,
    )

    if result["status"] != "completed":
        return {
            "prd_draft": f"## LỖI: Agent thất bại — {result['log']}",
            "status": "failed",
            "error": result["log"],
        }

    prd_draft = result["output"]
    save_prd(thread_id, prd_draft)
    node_stats = update_node_stats(
        state.node_stats, "ba",
        reject_count=0,
        tokens_used=result["prompt_tokens"] + result["completion_tokens"],
        model=result["model"],
    )
    content_history = push_content_history(state.content_history, "ba", prd_draft)

    return {
        "prd_draft": prd_draft,
        "status": "running",
        "gate_decision": None,
        "current_gate": "",
        "node_stats": node_stats,
        "content_history": content_history,
    }


def ba_node(state: SoftwareFactoryState, config: RunnableConfig | None = None) -> Dict[str, Any]:
    """Node BA: Phân tích raw_requirements → prd_draft.

    Args:
        state: SoftwareFactoryState hiện tại
        config: LangGraph configurable chứa thread_id (được inject tự động)

    Returns:
        Dict chứa prd_draft đã được LLM/Agent phân tích

    Bật/tắt nhánh agentic (OpenHands SDK) qua biến môi trường BA_USE_AGENT=true —
    mặc định TẮT (dùng cách cũ) để không phá vỡ hành vi hiện tại khi chưa test kỹ
    nhánh mới với LLM thật.
    """
    # Lấy thread_id từ config (LangGraph inject khi hàm có parameter config)
    # RunnableConfig có cấu trúc {"configurable": {"thread_id": "...", ...}}
    # KHÔNG dùng isinstance(config, dict) vì RunnableConfig là TypedDict luôn là dict
    thread_id = "default"
    if config:
        configurable = config.get("configurable", {}) or {}
        thread_id = configurable.get("thread_id", "default")

    raw_req = state.raw_requirements.strip()

    if not raw_req:
        return {
            "prd_draft": "## LỖI: Không có yêu cầu đầu vào. Vui lòng nhập yêu cầu.",
            "status": "failed",
            "error": "raw_requirements is empty",
        }

    feedback = _get_feedback(state)
    debate_synthesis = state.debate_synthesis.get("ba", "")

    use_agent = os.getenv("BA_USE_AGENT", "false").strip().lower() in ("1", "true", "yes")
    if use_agent:
        return _ba_node_agentic(state, thread_id, raw_req, feedback, debate_synthesis)
    return _ba_node_simple(state, thread_id, raw_req, feedback, debate_synthesis)


# Alias để dùng trong graph builder
BA_NODE = ba_node