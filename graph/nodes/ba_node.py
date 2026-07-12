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
    """Lấy phản hồi chỉnh sửa gần nhất cho gate_prd từ gate_history, nếu có."""
    if not state.gate_history:
        return ""
    prd_gates = [h for h in state.gate_history if h.get("gate") == "gate_prd"]
    if not prd_gates:
        return ""
    last_gate = prd_gates[-1]
    if last_gate.get("decision") in ["edit", "reject"]:
        return last_gate.get("note", "")
    return ""


def _ba_node_simple(state: SoftwareFactoryState, thread_id: str, raw_req: str, feedback: str) -> Dict[str, Any]:
    """Cách cũ: 1 lệnh gọi LLM, không tool, không kế hoạch. Đây là baseline để A/B
    so sánh với nhánh agentic — KHÔNG xoá, giữ nguyên để dễ rollback."""
    provider_name = os.getenv("BA_PROVIDER", None)
    llm = llm_factory(provider_name)

    system_prompt = load_prompt("ba_system")
    user_prompt = f"## YÊU CẦU KHÁCH HÀNG\n\n{raw_req}\n\n"
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
        "pending_gate_role": "",
        "node_stats": node_stats,
        "content_history": content_history,
    }


def _ba_node_agentic(state: SoftwareFactoryState, thread_id: str, raw_req: str, feedback: str) -> Dict[str, Any]:
    """Cách mới: dùng OpenHands SDK Agent thật (FileEditorTool + TaskTrackerTool),
    có kế hoạch, có tự đọc lại/tự sửa, và — khác biệt quan trọng nhất so với bản cũ —
    ĐỌC PRD CŨ khi có feedback thay vì viết lại từ đầu (gap #1 trong tài liệu kiến trúc).

    ⚠️ Nhánh này CHƯA được test với LLM thật (chưa có mạng/API key trong môi trường
    viết code) — chỉ mới verify import/API tĩnh. Bật thử bằng BA_USE_AGENT=true và
    theo dõi kỹ log trước khi tin tưởng dùng thật.
    """
    from graph.agent_runtime import run_agent

    workspace_root = Path(__file__).resolve().parent.parent.parent / "sandbox" / "workspace"
    workspace_path = workspace_root / thread_id / "ba_work"

    # Build Skill từ đúng nội dung prompts/system/ba_system.txt hiện có — KHÔNG viết
    # lại quy ước PRD từ đầu, chỉ đổi CÁCH đưa nó vào agent (qua Skill có trigger,
    # thay vì nhét cứng vào system_prompt của 1 lệnh gọi đơn).
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

    instructions = f"""Đọc kỹ yêu cầu khách hàng dưới đây và viết PRD vào file PRD.md.

## YÊU CẦU KHÁCH HÀNG
{raw_req}
{feedback_block}{prev_prd_block}
Quy ước cấu trúc PRD (BẮT BUỘC tuân theo):
{ba_prompt_content}

Quy trình làm việc:
1. Dùng task tracker lập kế hoạch trước khi viết bất cứ thứ gì.
2. {"Đọc bản PRD cũ ở trên, xác định đúng phần cần sửa theo phản hồi, sửa TRÊN BẢN ĐÓ." if feedback else "Viết PRD.md hoàn chỉnh theo đúng cấu trúc quy định."}
3. Đọc lại PRD.md vừa viết/sửa, tự kiểm tra: có thiếu yêu cầu nào từ đề bài gốc
   không, có mâu thuẫn nội bộ không. Sửa lại nếu cần — đừng chỉ liệt kê vấn đề
   rồi bỏ qua.
4. Khi thực sự hoàn tất, dừng lại.
"""

    cfg = {
        "usage_id": "ba-agent",
        "model": os.getenv("BA_LLM_MODEL", os.getenv("NVIDIA_MODEL", "openai/gpt-oss-120b")),
        "api_key": os.getenv("BA_LLM_API_KEY", os.getenv("NVIDIA_API_KEY", "")),
        "base_url": os.getenv("BA_LLM_BASE_URL", os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")),
        "max_iteration_per_run": int(os.getenv("BA_MAX_ITERATIONS", "30")),
    }

    result = run_agent(
        "openhands_text",
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
        "pending_gate_role": "",
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

    use_agent = os.getenv("BA_USE_AGENT", "false").strip().lower() in ("1", "true", "yes")
    if use_agent:
        return _ba_node_agentic(state, thread_id, raw_req, feedback)
    return _ba_node_simple(state, thread_id, raw_req, feedback)


# Alias để dùng trong graph builder
BA_NODE = ba_node