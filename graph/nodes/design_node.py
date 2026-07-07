"""Node Design — Technical Designer: tạo Design Document từ PRD."""
import os
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig

from graph.state import (
    SoftwareFactoryState,
    count_rejects,
    update_node_stats,
    push_content_history,
)
from graph.llm import llm_factory
from graph.artifact_store import save_design, read_design, save_prd, read_prd, read_gate_feedback
from graph.prompt_loader import load_prompt



def design_node(state: SoftwareFactoryState, config: RunnableConfig | None = None) -> Dict[str, Any]:
    """Chuyển prd_approved/prd_v1 → design_doc.
    
    Args:
        state: SoftwareFactoryState hiện tại
        config: LangGraph configurable chứa thread_id (được inject tự động)
    
    Returns a dict with:
        - design_doc (Markdown)
        - status (running/failed)
        - error (optional)
    """
    # Lấy thread_id từ config (LangGraph inject khi hàm có parameter config)
    # RunnableConfig có cấu trúc {"configurable": {"thread_id": "...", ...}}
    # KHÔNG dùng isinstance(config, dict) vì RunnableConfig là TypedDict luôn là dict
    thread_id = "default"
    if config:
        configurable = config.get("configurable", {}) or {}
        thread_id = configurable.get("thread_id", "default")
    
    prd = state.prd_approved.strip() or state.prd_v1.strip()
    if not prd:
        # Fallback: đọc từ Artifact Store
        prd = read_prd(thread_id)
    
    if not prd:
        return {
            "design_doc": "## LỖI: Không có PRD được duyệt để tạo Design. Vui lòng chạy PRD node trước.",
            "status": "failed",
            "error": "prd_v1 and prd_approved are empty",
        }
    
    # Kiểm tra và đọc lịch sử feedback từ file (toàn bộ, không chỉ bản gần nhất)
    feedback_history = read_gate_feedback(thread_id, "gate_design")

    # Provider có thể được override qua env
    provider_name = os.getenv("DESIGN_PROVIDER", None)
    llm = llm_factory(provider_name)

    system_prompt = load_prompt("design_system")
    user_prompt = f"## PRD ĐÃ DUYỆT\n\n{prd}\n\n"
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
    
    # Lưu kết quả vào Artifact Store
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

# Alias để GraphBuilder dùng
DESIGN_NODE = design_node