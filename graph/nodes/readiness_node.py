"""Node Readiness Check — kiểm tra nhất quán CHÉO giữa PRD/UX/Design/Mockup
TRƯỚC khi engineer bắt đầu sinh code. Chạy sau gate_mockup(approve), trước
gate_readiness (gate người, luôn xảy ra — không tự động bỏ qua).

Khác critic_prd/critic_design (review 1 artifact): đây review SỰ NHẤT QUÁN
giữa NHIỀU artifact — mirror bmm-skills/3-solutioning/
bmad-check-implementation-readiness/steps/* (đã verify), đặc biệt step
"ux-alignment" (PRD<->UX<->Architecture có khớp không, UI được ngụ ý mà
thiếu UX Spec tương ứng thì cảnh báo).

Không dùng triage 5 nhóm / không tự động loop_upstream — LUÔN đi tiếp
gate_readiness để người quyết định (đúng tinh thần checkpoint-preview.md:
máy chỉ gắn tag/tổng hợp, không tự quyết định thay người ở gate cuối cùng
trước khi tốn token sinh code).
"""
from typing import Any, Dict, Optional

from langchain_core.runnables import RunnableConfig

from graph.state import SoftwareFactoryState, update_critic_reports
from graph.critic import CriticLens, run_critic_pass

NODE_NAME = "readiness"

_LENSES = [
    CriticLens(
        id="readiness_auditor",
        name="Readiness Auditor",
        system_prompt=(
            "Bạn là Readiness Auditor — kiểm tra SỰ NHẤT QUÁN CHÉO giữa 4 "
            "artifact dưới đây (PRD / UX Spec / Design Document / Mockup) "
            "TRƯỚC khi bắt đầu code. Đây KHÔNG phải review từng artifact "
            "riêng lẻ (đã có critic_prd/critic_design lo việc đó) — chỉ tập "
            "trung vào ĐIỂM NỐI giữa chúng:\n\n"
            "1. PRD <-> UX: mọi FR trong PRD có màn hình/flow tương ứng "
            "trong UX Spec không? Có FR ngụ ý cần UI mà UX Spec không có "
            "màn hình nào phục vụ không?\n"
            "2. UX <-> Design: danh sách màn hình trong Design Document có "
            "khớp UX Spec không (đã có critic_design kiểm rồi, chỉ xác nhận "
            "lại nhanh, không lặp lại chi tiết)?\n"
            "3. Design <-> Mockup: mockup HTML có đủ các màn hình mà Design "
            "Document liệt kê không, hay thiếu/thừa màn hình?\n"
            "4. PRD <-> Mockup: có tính năng nào PRD mô tả rõ ràng nhưng "
            "hoàn toàn không xuất hiện dấu vết gì trong mockup không?\n\n"
            "Chỉ nêu finding có bằng chứng cụ thể (trích tên màn hình/FR-ID "
            "bị lệch), không suy đoán. Nếu cả 4 khía cạnh đều nhất quán, ghi "
            "VERDICT: ok."
        ),
    ),
]


def _thread_id_from_config(config: Optional[RunnableConfig]) -> str:
    if not config:
        return "default"
    return (config.get("configurable", {}) or {}).get("thread_id", "default")


def readiness_node(
    state: SoftwareFactoryState, config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    thread_id = _thread_id_from_config(config)

    artifact_text = (
        f"## PRD\n\n{state.prd_approved or state.prd_v1}\n\n"
        f"## UX SPEC\n\n{state.ux_spec}\n\n"
        f"## DESIGN DOCUMENT\n\n{state.design_doc}\n\n"
        f"## MOCKUP (tóm tắt — danh sách file/screens đã sinh)\n\n"
        f"{_summarize_mockup(state)}"
    )

    summary = run_critic_pass(
        thread_id=thread_id,
        node_name=NODE_NAME,
        artifact_text=artifact_text,
        lenses=_LENSES,
        context="",
    )

    return {
        "critic_reports": update_critic_reports(state.critic_reports, NODE_NAME, summary),
    }


def _summarize_mockup(state: SoftwareFactoryState) -> str:
    """Mockup HTML có thể rất dài (nhiều file) — chỉ đưa tên file, không đưa
    nguyên văn HTML vào prompt (tốn token vô ích cho lens này, vốn chỉ cần
    biết CÓ những màn hình nào, không cần xem chi tiết UI)."""
    screens = getattr(state, "mockup_screens", None) or {}
    if screens:
        return "\n".join(f"- {name}" for name in screens.keys())
    html = getattr(state, "mockup_html", "") or ""
    if html:
        return f"(Không có danh sách screens tường minh — mockup_html dài {len(html)} ký tự)"
    return "(Không có mockup)"


READINESS_NODE = readiness_node
