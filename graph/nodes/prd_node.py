"""Node PRD — Product Manager: tạo PRD chi tiết từ ba_draft."""
import os
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig

from graph.state import SoftwareFactoryState
from graph.llm import llm_factory
from graph.artifact_store import (
    save_prd, read_prd,
    save_design, read_design,
    save_mockup, read_mockup,
    save_test_report, read_test_report,
    save_test_results, read_test_results,
    save_engineer_log, read_engineer_log,
    save_manifest, read_manifest,
    list_artifacts,
    read_gate_feedback,
)
from graph.prompt_loader import load_prompt



def prd_node(state: SoftwareFactoryState, config: RunnableConfig | None = None) -> Dict[str, Any]:
    """Chuyển ba_draft → prd_v1 (phiên bản PRD).
    
    Args:
        state: SoftwareFactoryState hiện tại
        config: LangGraph configurable chứa thread_id (được inject tự động)
    
    Trả về dict có khóa:
        - prd_v1 (Markdown PRD)
        - status (running/failed)
        - error (nếu có)
    """
    # Lấy thread_id từ config (LangGraph inject khi hàm có parameter config)
    # RunnableConfig có cấu trúc {"configurable": {"thread_id": "...", ...}}
    # KHÔNG dùng isinstance(config, dict) vì RunnableConfig là TypedDict luôn là dict
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
        # Nếu state.prd_draft khác với cached, ưu tiên state.prd_draft (mới hơn)
        pass
    
    if not ba_draft:
        return {
            "prd_v1": "## LỖI: Không có ba_draft để viết PRD. Vui lòng chạy BA node trước.",
            "status": "failed",
            "error": "prd_draft is empty",
        }
    
    # Lấy provider (có thể override bằng env PRD_PROVIDER)
    provider_name = os.getenv("PRD_PROVIDER", None)
    llm = llm_factory(provider_name)

    system_prompt = load_prompt("prd_system")
    user_prompt = (
        "## Bản phân tích BA (ba_draft)\n\n" + ba_draft + "\n\n"
        "Hãy viết SRS chi tiết dựa trên nội dung trên."
    )

    # Đọc toàn bộ lịch sử feedback từ file (thay thế việc chỉ đọc gate_history gần nhất)
    feedback_history = read_gate_feedback(thread_id, "gate_prd")
    if feedback_history:
        user_prompt += (
            "\n\n## LỊCH SỬ NHẬN XÉT TỪ REVIEWER\n"
            + feedback_history
            + "\nLưu ý các nhận xét trên khi viết lại tài liệu.\n"
        )
    
    result = llm.call(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=20000,
    )
    
    if result is None:
        return {
            "prd_v1": "## LỖI: LLM không trả về kết quả PRD.",
            "status": "failed",
            "error": "LLM returned None",
        }
    
    # Lưu kết quả vào Artifact Store
    save_prd(thread_id, result)
    
    return {"prd_v1": result, "status": "running"}

# Alias để GraphBuilder dùng
PRD_NODE = prd_node
