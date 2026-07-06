"""Node PRD — Product Manager: tạo PRD chi tiết từ ba_draft."""
import os
from typing import Dict, Any
from datetime import datetime
from langchain_core.runnables import RunnableConfig

from graph.state import SoftwareFactoryState, MAX_HISTORY_VERSIONS
from graph.llm import llm_factory
from graph.stats_utils import count_rejects
from graph.artifact_store import (
    save_prd, read_prd,
    read_gate_feedback,
)
from graph.prompt_loader import load_prompt


# Mapping node_name → gate_name để tính reject_count
_NODE_GATES = {
    "ba": None,
    "prd": "gate_prd",
    "design": "gate_design",
    "ui": "gate_mockup",
}


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
    
    llm_response = llm.call(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=20000,
    )
    result = llm_response.content or ""
    
    if not result:
        return {
            "prd_v1": "## LỖI: LLM không trả về kết quả PRD.",
            "status": "failed",
            "error": "LLM returned None",
        }
    
    # Lưu kết quả vào Artifact Store
    save_prd(thread_id, result)
    
    # --- Cập nhật node_stats ---
    node_name = "prd"
    gate_name = _NODE_GATES.get(node_name)
    
    stats = dict(state.node_stats)
    existing = stats.get(node_name, {})
    stats[node_name] = {
        "reject_count": count_rejects(state.gate_history, gate_name) if gate_name else 0,
        "tokens_used": existing.get("tokens_used", 0) + llm_response.total_tokens,
        "model": llm_response.model,
    }

    # --- Cập nhật content_history ---
    all_history = dict(state.content_history)
    history = list(all_history.get(node_name, []))
    history.insert(0, {"content": result, "timestamp": datetime.now().isoformat()})
    history = history[:MAX_HISTORY_VERSIONS]
    all_history[node_name] = history

    return {
        "prd_v1": result,
        "status": "running",
        "node_stats": stats,
        "content_history": all_history,
    }

# Alias để GraphBuilder dùng
PRD_NODE = prd_node
