"""Node PRD — Product Manager: tạo PRD chi tiết từ ba_draft."""
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
    save_prd, read_prd,
    save_design, read_design,
    save_test_report, read_test_report,
    save_test_results, read_test_results,
    save_engineer_log, read_engineer_log,
    save_manifest, read_manifest,
    list_artifacts,
    read_gate_feedback,
)
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


def _prd_node_simple(state: SoftwareFactoryState, thread_id: str, ba_draft: str, feedback: str) -> Dict[str, Any]:
    """Cách cũ: 1 lệnh gọi LLM, không tool, không kế hoạch."""
    provider_name = os.getenv("PRD_PROVIDER", None)
    llm = llm_factory(provider_name)

    system_prompt = load_prompt("prd_system")
    user_prompt = (
        "## Bản phân tích BA (ba_draft)\n\n" + ba_draft + "\n\n"
        "Hãy viết SRS chi tiết dựa trên nội dung trên."
    )

    if feedback:
        user_prompt += (
            f"\n\n## PHẢN HỒI YÊU CẦU CHỈNH SỬA TỪ BẢN DUYỆT TRƯỚC\n"
            f"Người duyệt đã yêu cầu chỉnh sửa với ý kiến sau:\n"
            f"\"{feedback}\"\n\n"
            f"Hãy cập nhật lại tài liệu PRD để đáp ứng phản hồi trên."
        )
    else:
        # Đọc toàn bộ lịch sử feedback từ file (thay thế việc chỉ đọc gate_history gần nhất)
        feedback_history = read_gate_feedback(thread_id, "gate_prd")
        if feedback_history:
            user_prompt += (
                "\n\n## LỊCH SỬ NHẬN XÉT TỪ REVIEWER\n"
                + feedback_history
                + "\nLưu ý các nhận xét trên khi viết lại tài liệu.\n"
            )

    llm_response = llm.call(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=20000,
    )
    result = llm_response.content

    if result is None:
        return {
            "prd_v1": "## LỖI: LLM không trả về kết quả PRD.",
            "status": "failed",
            "error": "LLM returned None",
        }

    save_prd(thread_id, result)
    node_stats = update_node_stats(
        state.node_stats, "prd",
        reject_count=count_rejects(state.gate_history, "gate_prd"),
        tokens_used=llm_response.total_tokens,
        model=llm_response.model,
    )
    content_history = push_content_history(state.content_history, "prd", result)

    return {
        "prd_v1": result,
        "status": "running",
        "node_stats": node_stats,
        "content_history": content_history,
    }


def _prd_node_agentic(state: SoftwareFactoryState, thread_id: str, ba_draft: str, feedback: str) -> Dict[str, Any]:
    """Cách mới: dùng OpenCode agent (opencode serve HTTP REST) — đơn giản, đã test
    thành công. Agent tự đọc file, lập kế hoạch, viết PRD.md, tự kiểm tra và tự sửa.
    """
    from graph.agent_runtime import run_agent
    from graph.repo_store import AGENT_WORKSPACE_ROOT

    # Workspace trong AGENT_WORKSPACE_ROOT/<threadID>/prd_work
    workspace_path = AGENT_WORKSPACE_ROOT / thread_id / "prd_work"

    prd_prompt_content = load_prompt("prd_system")

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

    instructions = f"""Read the BA analysis below and write a detailed PRD (SRS) into file PRD.md.

## BẢN PHÂN TÍCH BA (ba_draft)
{ba_draft}
{feedback_block}{prev_prd_block}
Quy ước cấu trúc PRD (BẮT BUỘC tuân theo):
{prd_prompt_content}

Quy trình làm việc:
1. {"Đọc bản PRD cũ ở trên, xác định đúng phần cần sửa theo phản hồi, sửa TRÊN BẢN ĐÓ." if feedback else "Viết PRD.md hoàn chỉnh theo đúng cấu trúc quy định."}
2. Đọc lại PRD.md vừa viết/sửa, tự kiểm tra: có thiếu yêu cầu nào từ đề bài gốc
   không, có mâu thuẫn nội bộ không. Sửa lại nếu cần.
3. Khi thực sự hoàn tất, dừng lại.
"""

    cfg = {
        "model": os.getenv("PRD_LLM_MODEL", os.getenv("NVIDIA_MODEL", "openai/gpt-oss-120b")),
        "api_key": os.getenv("PRD_LLM_API_KEY", os.getenv("NVIDIA_API_KEY", "")),
        "base_url": os.getenv("PRD_LLM_BASE_URL", os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")),
    }

    result = run_agent(
        "opencode",
        {"instructions": instructions, "workspace_path": workspace_path, "output_file": "PRD.md"},
        cfg,
    )

    if result["status"] != "completed":
        return {
            "prd_v1": f"## LỖI: Agent thất bại — {result['log']}",
            "status": "failed",
            "error": result["log"],
        }

    prd_v1 = result["output"]
    save_prd(thread_id, prd_v1)
    node_stats = update_node_stats(
        state.node_stats, "prd",
        reject_count=count_rejects(state.gate_history, "gate_prd"),
        tokens_used=result["prompt_tokens"] + result["completion_tokens"],
        model=result["model"],
    )
    content_history = push_content_history(state.content_history, "prd", prd_v1)

    return {
        "prd_v1": prd_v1,
        "status": "running",
        "node_stats": node_stats,
        "content_history": content_history,
    }


def prd_node(state: SoftwareFactoryState, config: RunnableConfig | None = None) -> Dict[str, Any]:
    """Chuyển ba_draft → prd_v1 (phiên bản PRD).

    Bật/tắt nhánh agentic (OpenCode) qua biến môi trường PRD_USE_AGENT=true —
    mặc định TẮT (dùng cách cũ) để không phá vỡ hành vi hiện tại.
    
    Args:
        state: SoftwareFactoryState hiện tại
        config: LangGraph configurable chứa thread_id (được inject tự động)
    
    Trả về dict có khóa:
        - prd_v1 (Markdown PRD)
        - status (running/failed)
        - error (nếu có)
    """
    # Lấy thread_id từ config (LangGraph inject khi hàm có parameter config)
    thread_id = "default"
    if config:
        configurable = config.get("configurable", {}) or {}
        thread_id = configurable.get("thread_id", "default")

    # Ưu tiên đọc từ Artifact Store trước, fallback về state.prd_draft
    ba_draft = state.prd_draft.strip()
    cached_prd = read_prd(thread_id)
    if cached_prd and not ba_draft:
        ba_draft = cached_prd
    elif cached_prd:
        pass

    if not ba_draft:
        return {
            "prd_v1": "## LỖI: Không có ba_draft để viết PRD. Vui lòng chạy BA node trước.",
            "status": "failed",
            "error": "prd_draft is empty",
        }

    feedback = _get_feedback(state)

    use_agent = os.getenv("PRD_USE_AGENT", "false").strip().lower() in ("1", "true", "yes")
    if use_agent:
        return _prd_node_agentic(state, thread_id, ba_draft, feedback)
    return _prd_node_simple(state, thread_id, ba_draft, feedback)


# Alias để GraphBuilder dùng
PRD_NODE = prd_node
