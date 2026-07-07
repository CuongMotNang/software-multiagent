"""Node BA — Business Analyst: phân tích yêu cầu thô → PRD draft."""
import os
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from graph.state import (
    SoftwareFactoryState,
    update_node_stats,
    push_content_history,
)
from graph.llm import llm_factory
from graph.artifact_store import save_prd, read_prd
from graph.prompt_loader import load_prompt



def ba_node(state: SoftwareFactoryState, config: RunnableConfig | None = None) -> Dict[str, Any]:
    """Node BA: Phân tích raw_requirements → prd_draft.
    
    Args:
        state: SoftwareFactoryState hiện tại
        config: LangGraph configurable chứa thread_id (được inject tự động)
        
    Returns:
        Dict chứa prd_draft đã được LLM phân tích
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
    
    # Kiểm tra phản hồi chỉnh sửa gần nhất cho gate_prd từ gate_history
    feedback = ""
    if state.gate_history:
        prd_gates = [h for h in state.gate_history if h.get("gate") == "gate_prd"]
        if prd_gates:
            last_gate = prd_gates[-1]
            if last_gate.get("decision") in ["edit", "reject"]:
                feedback = last_gate.get("note", "")
    
    # Lấy LLM provider (mặc định nvidia, có thể override qua env BA_PROVIDER)
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
    
    # Gọi LLM
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
    
    # Lưu kết quả vào Artifact Store (dùng thread_id từ config)
    save_prd(thread_id, result)

    # ── Observability: token/model/history ──
    # Lưu ý: "ba" không có gate riêng ngay sau nó (edge thật là
    # ba -> prd -> gate_prd, gate_prd review output của "prd" chứ không
    # phải của "ba") nên reject_count của ba luôn = 0.
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


# Alias để dùng trong graph builder
BA_NODE = ba_node