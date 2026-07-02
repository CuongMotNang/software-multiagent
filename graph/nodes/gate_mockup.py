"""Node Gate Mockup — Cổng duyệt Mockup UI của Business Analyst."""
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from langgraph.types import interrupt
from langchain_core.runnables import RunnableConfig
from graph.state import SoftwareFactoryState
from graph.artifact_store import _artifact_dir, save_gate_feedback

def gate_mockup(state: SoftwareFactoryState, config: RunnableConfig | None = None) -> Dict[str, Any]:
    """Cổng duyệt Mockup UI: Sử dụng dynamic interrupt để tạm dừng và chờ duyệt từ BA."""
    # Set gate ngay trước khi interrupt để UI biết đang dừng ở đâu
    updates = {
        "current_gate": "gate_mockup",
        "pending_gate_role": "ba",
    }
    
    # Lấy thread_id từ config (LangGraph inject khi hàm có parameter config)
    thread_id = "default"
    if config:
        configurable = config.get("configurable", {}) or {}
        thread_id = configurable.get("thread_id", "default")
    
    # Đường dẫn thư mục artifact — BA tự mở thư mục xem file
    artifact_dir = str(_artifact_dir(thread_id))
    
    # Gọi interrupt để dừng luồng và truyền payload thông tin duyệt
    decision = interrupt({
        "gate": "gate_mockup",
        "role": "ba",
        "artifact_dir": artifact_dir,
    })
    
    # Nhận giá trị từ Command(resume=...)
    action = decision.get("action")
    feedback = decision.get("feedback", "")
    
    history_entry = {
        "gate": "gate_mockup",
        "role": "ba",
        "decision": action,
        "note": feedback,
        "timestamp": datetime.now().isoformat()
    }
    
    updates["gate_decision"] = action
    updates["gate_history"] = [history_entry]

    # Persist feedback ra file để LLM đọc lại ở lần chạy tiếp theo
    if action in ("reject", "edit") and feedback:
        save_gate_feedback(thread_id, "gate_mockup", feedback, action)

    # Clear gate flag khi đã xử lý xong
    updates["current_gate"] = ""
    updates["pending_gate_role"] = ""
    
    return updates

# Alias
GATE_MOCKUP = gate_mockup
