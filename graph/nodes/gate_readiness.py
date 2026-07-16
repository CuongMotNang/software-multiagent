"""Node Gate Readiness — Cổng duyệt CUỐI CÙNG trước khi engineer sinh code.

Người luôn xem qua readiness_report (đã tổng hợp bởi readiness_node) trước
khi cho phép tốn token sinh code. Approve -> engineer. Reject/Edit -> quay
lại "design" (đúng nguyên tắc backward-loop: lỗi cross-artifact thường bắt
nguồn từ thiết kế, không phải mockup — mockup chỉ theo design mà làm).
"""
from datetime import datetime
from typing import Dict, Any
from langgraph.types import interrupt
from graph.state import SoftwareFactoryState
from graph.repo_store import save_gate_feedback


def gate_readiness(state: SoftwareFactoryState) -> Dict[str, Any]:
    updates = {
        "current_gate": "gate_readiness",
        "pending_gate_role": "lead",
    }

    decision = interrupt({
        "gate": "gate_readiness",
        "role": "lead",
        "readiness_report": state.critic_reports.get("readiness", {}),
    })

    action = decision.get("action")
    feedback = decision.get("feedback", "")

    history_entry = {
        "gate": "gate_readiness",
        "role": "lead",
        "decision": action,
        "note": feedback,
        "timestamp": datetime.now().isoformat()
    }

    updates["gate_decision"] = action
    updates["gate_history"] = [history_entry]

    if action in ("reject", "edit") and feedback:
        thread_id = "default"
        if hasattr(state, "thread_id") and state.thread_id:
            thread_id = state.thread_id
        save_gate_feedback(thread_id, "gate_readiness", feedback, action)

    updates["current_gate"] = ""
    updates["pending_gate_role"] = ""

    return updates


GATE_READINESS = gate_readiness


def route_gate_readiness(state: SoftwareFactoryState) -> str:
    """Approve -> engineer. Reject/Edit -> quay lại "design" (backward-loop
    thật, không tự-loop tại readiness_node vì readiness_node không tự viết
    lại artifact nào)."""
    decision = state.get("gate_decision") if isinstance(state, dict) else state.gate_decision
    if decision == "approve":
        return "engineer"
    return "design"
