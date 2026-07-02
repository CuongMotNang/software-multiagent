"""Node Gate Design — Cổng duyệt thiết kế của Lead Developer."""
from datetime import datetime
from typing import Dict, Any
from langgraph.types import interrupt
from graph.state import SoftwareFactoryState
from graph.artifact_store import save_gate_feedback

def gate_design(state: SoftwareFactoryState) -> Dict[str, Any]:
    """Cổng duyệt Thiết kế: Sử dụng dynamic interrupt để tạm dừng và chờ duyệt từ Dev."""
    # Set gate ngay trước khi interrupt để UI biết đang dừng ở đâu
    updates = {
        "current_gate": "gate_design",
        "pending_gate_role": "dev",
    }
    
    # Gọi interrupt để dừng luồng và truyền payload thông tin duyệt
    decision = interrupt({
        "gate": "gate_design",
        "role": "dev",
        "design_doc": state.design_doc,
    })
    
    # Nhận giá trị từ Command(resume=...)
    action = decision.get("action")
    feedback = decision.get("feedback", "")
    
    history_entry = {
        "gate": "gate_design",
        "role": "dev",
        "decision": action,
        "note": feedback,
        "timestamp": datetime.now().isoformat()
    }
    
    updates["gate_decision"] = action
    updates["gate_history"] = [history_entry]

    # Persist feedback ra file để LLM đọc lại ở lần chạy tiếp theo
    if action in ("reject", "edit") and feedback:
        thread_id = "default"
        if hasattr(state, "thread_id") and state.thread_id:
            thread_id = state.thread_id
        save_gate_feedback(thread_id, "gate_design", feedback, action)

    # Clear gate flag khi đã xử lý xong
    updates["current_gate"] = ""
    updates["pending_gate_role"] = ""
    
    return updates

# Alias
GATE_DESIGN = gate_design
