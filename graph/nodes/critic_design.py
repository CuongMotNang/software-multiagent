"""Node Critic Design — parallel critic pass + triage cho design_doc.

Chạy SAU design_node, TRƯỚC gate_design. Mirror đúng quan hệ critic_prd -> gate_prd.

3 lens dưới đây lấy từ bmm-skills/3-solutioning/bmad-architecture/references/
reviewer-gate.md (đã verify trực tiếp) — đặc biệt lens "Operational Envelope"
lấy nguyên ý từ BMAD: 1 khía cạnh im lặng hoàn toàn (không nhắc gì tới
deployment/infra/vận hành) tự nó ĐÃ LÀ 1 finding, không cần đợi có lỗi cụ thể.
"""
from typing import Any, Dict, Optional

from langchain_core.runnables import RunnableConfig

from graph.state import (
    SoftwareFactoryState,
    update_critic_reports,
    update_triage_action,
    bump_review_loop_iteration,
    reset_review_loop_iteration,
    set_upstream_feedback,
    clear_upstream_feedback,
)
from graph.critic import CriticLens, run_critic_pass
from graph.triage import classify_findings, decide_routing

NODE_NAME = "design"

_LENSES = [
    CriticLens(
        id="consistency",
        name="Consistency & Divergence Critic",
        system_prompt=(
            "Bạn là Consistency Critic cho Design Document dưới đây. Kiểm "
            "tra tính nhất quán NỘI BỘ giữa các phần: Process Model có khớp "
            "với Data Model không (VD: 1 flow nhắc tới field/entity không "
            "tồn tại trong Data Model)? Quan hệ nhiều-nhiều (many-to-many) "
            "có bảng trung gian (junction table) chưa hay bị bỏ sót? API "
            "endpoint có phủ đủ các thao tác mà Process Model mô tả không? "
            "Chỉ nêu finding có bằng chứng cụ thể (trích vị trí/section), "
            "không suy đoán điều Design Document không nói tới."
        ),
    ),
    CriticLens(
        id="operational_envelope",
        name="Operational Envelope Critic",
        system_prompt=(
            "Bạn là Operational Envelope Critic. Đây KHÔNG phải kiểm tra "
            "lỗi cụ thể, mà kiểm tra XEM CÓ 1 KHÍA CẠNH NÀO BỊ IM LẶNG HOÀN "
            "TOÀN không — 1 khía cạnh im lặng hoàn toàn TỰ NÓ ĐÃ LÀ 1 "
            "finding, không cần đợi có sai sót cụ thể mới báo:\n"
            "1. Deployment & environments — Design Document có nhắc gì tới "
            "môi trường chạy (dev/staging/production), cách deploy không?\n"
            "2. Infra/provider strategy — có nói tới hosting/database "
            "provider, hay hoàn toàn không đề cập?\n"
            "3. Operations — có tính tới logging/monitoring/backup không, "
            "hay bỏ qua hoàn toàn?\n"
            "Với mỗi khía cạnh bị im lặng hoàn toàn, ghi finding dạng: "
            "'Design Document không đề cập gì tới X' — mức độ nghiêm trọng "
            "tuỳ vào độ quan trọng của X với dự án cụ thể này (đọc PRD để "
            "đánh giá, không đánh đồng mọi dự án đều cần đủ cả 3)."
        ),
    ),
    CriticLens(
        id="seam_with_ux",
        name="Seam Reviewer (UX <-> Design)",
        system_prompt=(
            "Bạn là Seam Reviewer, chuyên soi điểm nối giữa UX Spec (đưa "
            "trong phần NGỮ CẢNH, do Sally viết) và Design Document (đưa "
            "trong phần NỘI DUNG CẦN REVIEW, do Winston viết). Kiểm tra: "
            "danh sách màn hình trong Design Document có ĐÚNG Y NGUYÊN danh "
            "sách từ UX Spec không (không được tự thêm/bớt/đổi tên)? 'Ghi "
            "chú cho Architect' trong UX Spec (các ràng buộc UX ảnh hưởng "
            "kiến trúc, VD: cần real-time update, optimistic UI, phân "
            "trang) có được Data Model/API tính tới chưa? Nếu Design "
            "Document hoàn toàn nhất quán với UX Spec, ghi VERDICT: ok."
        ),
    ),
]


def _thread_id_from_config(config: Optional[RunnableConfig]) -> str:
    if not config:
        return "default"
    return (config.get("configurable", {}) or {}).get("thread_id", "default")


def critic_design(
    state: SoftwareFactoryState, config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    thread_id = _thread_id_from_config(config)

    summary = run_critic_pass(
        thread_id=thread_id,
        node_name=NODE_NAME,
        artifact_text=state.design_doc,
        lenses=_LENSES,
        context=f"## UX SPEC\n\n{state.ux_spec}",
    )

    findings = classify_findings(summary)
    loop_iter = state.review_loop_iteration.get(NODE_NAME, 0)
    routing = decide_routing(findings, loop_iteration=loop_iter)

    updates: Dict[str, Any] = {
        "critic_reports": update_critic_reports(state.critic_reports, NODE_NAME, summary),
        "triage_action": update_triage_action(state.triage_action, NODE_NAME, routing["action"]),
    }

    if routing["action"] == "loop_upstream":
        # bad_spec: gốc vấn đề nằm ở UX Spec (danh sách màn hình/ghi chú
        # không đủ rõ) -> quay lại "ux", không tự-loop trong "design".
        updates["review_loop_iteration"] = bump_review_loop_iteration(
            state.review_loop_iteration, NODE_NAME
        )
        updates["upstream_feedback"] = set_upstream_feedback(
            state.upstream_feedback,
            "ux",
            "Critic pass ở bước Design phát hiện Design Document không khớp "
            f"/ thiếu sót so với UX Spec:\n{routing['feedback']}",
        )
    elif routing["action"] == "auto_patch":
        # patch: sửa tại chỗ trong phạm vi Design, design_node tự chạy lại.
        updates["upstream_feedback"] = set_upstream_feedback(
            state.upstream_feedback,
            "design",
            f"Critic pass phát hiện cần sửa trực tiếp trong Design Document:\n{routing['feedback']}",
        )
    elif routing["action"] == "halt_escalate":
        updates["pending_escalation_questions"] = "\n".join(
            f"- {q}" for q in routing.get("questions", [])
        )
    else:  # proceed
        updates["review_loop_iteration"] = reset_review_loop_iteration(
            state.review_loop_iteration, NODE_NAME
        )
        updates["upstream_feedback"] = clear_upstream_feedback(
            state.upstream_feedback, "design"
        )

    return updates


CRITIC_DESIGN = critic_design
