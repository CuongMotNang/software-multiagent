"""Node Critic PRD — parallel critic pass + triage cho prd_v1.

Chạy SAU prd_node, TRƯỚC gate_prd. Không thay thế gate người — chỉ làm
giàu chất lượng trước khi tới gate, và quyết định có cần quay lại BA
(bad_spec), tự sửa tại chỗ (patch), hay phải dừng hỏi người (intent_gap)
trước khi trình gate_prd như bình thường.

3 lens dưới đây được nhóm lại từ rubric 7 CHIỀU thật của BMAD
(bmm-skills/2-plan-workflows/bmad-prd/assets/prd-validation-checklist.md,
đã verify trực tiếp) — không phải placeholder tên suông như bản trước.
Nguyên văn rubric có 7 chiều (decision-readiness, substance-over-theater,
strategic-coherence, done-ness-clarity, scope-honesty, downstream-usability,
shape-fit); gộp thành 3 lệnh gọi song song để không đội chi phí token:
  - Lens 1 (Judgment): decision-readiness + substance-over-theater +
    strategic-coherence + shape-fit — 4 chiều đòi hỏi PHÁN ĐOÁN chủ quan.
  - Lens 2 (Testability & Scope): done-ness-clarity + scope-honesty — 2
    chiều CƠ HỌC, kiểm được bằng bằng chứng cụ thể trong văn bản.
  - Lens 3 (Seam + Downstream): seam BA<->PRD (đặc thù pipeline của bạn,
    KHÔNG có trong BMAD) gộp với downstream-usability (glossary/ID nhất
    quán để Design/UX đọc tiếp được — CÓ trong BMAD).
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

NODE_NAME = "prd"

_LENSES = [
    CriticLens(
        id="judgment",
        name="Judgment Critic (decision-readiness / substance / coherence / shape-fit)",
        system_prompt=(
            "Bạn là PRD Judgment Critic. Đọc bản PRD dưới đây và chấm 4 khía "
            "cạnh cần PHÁN ĐOÁN chủ quan, có bằng chứng cụ thể (trích đoạn/vị "
            "trí), không tick-box:\n\n"
            "1. DECISION-READINESS: Người ra quyết định có hành động được "
            "trên PRD này không? Trade-off có bị nêu trung tính/né tránh "
            "không (VD: mọi lựa chọn đều 'cân bằng', mọi NFR đều 'quan "
            "trọng')? Open Questions có thực sự CÒN MỞ, hay là câu hỏi tu từ "
            "đã có sẵn câu trả lời ngay câu sau?\n"
            "2. SUBSTANCE OVER THEATER: Phát hiện nội dung 'trang trí' không "
            "phục vụ quyết định nào — persona không dẫn tới quyết định cụ "
            "thể nào trong PRD, NFR sáo rỗng kiểu 'phải scalable/secure' mà "
            "không có ngưỡng số cụ thể, tuyên bố khác biệt/đổi mới không có "
            "căn cứ.\n"
            "3. STRATEGIC COHERENCE: PRD có 1 luận điểm xuyên suốt (thesis) "
            "không, hay là danh sách feature rời rạc gắn tiêu đề section cho "
            "có? Success Metrics có thực sự đo đúng luận điểm đó không (VD: "
            "đo DAU/MAU trong khi luận điểm là về CHẤT LƯỢNG tương tác — đây "
            "là dấu hiệu lệch)?\n"
            "4. SHAPE FIT: PRD có bị ép vào khuôn sai loại sản phẩm không? "
            "Sản phẩm B2C/nhiều bên liên quan cần user journey có nhân vật "
            "cụ thể; tool nội bộ 1 người dùng thì user journey là thừa, cần "
            "dạng capability-spec thay vì kịch bản nhân vật.\n\n"
            "Chỉ nêu finding có bằng chứng cụ thể trong văn bản (trích vị "
            "trí/section), không suy đoán điều PRD không nói tới."
        ),
    ),
    CriticLens(
        id="testability_scope",
        name="Testability & Scope Critic (done-ness / scope-honesty)",
        system_prompt=(
            "Bạn là PRD Testability & Scope Critic — kiểm tra 2 khía cạnh CƠ "
            "HỌC, có thể đối chiếu trực tiếp với văn bản:\n\n"
            "1. DONE-NESS CLARITY: Với MỖI FR, có ít nhất 1 điều kiện kiểm "
            "được cụ thể (AC dạng Given/When/Then, hoặc số đo cụ thể) không? "
            "Liệt kê CHÍNH XÁC những FR nào chỉ ghi tính từ mơ hồ ('xử lý "
            "tốt', 'hiệu năng hợp lý', 'thân thiện với người dùng') mà không "
            "có ngưỡng/điều kiện kiểm được kèm theo — đây là dimension quan "
            "trọng nhất vì downstream (Design/Engineer) sẽ dựa vào đây nhiều "
            "nhất, hãy khắt khe.\n"
            "2. SCOPE HONESTY: Phần out-of-scope/giả định có được nêu RÕ "
            "RÀNG hay người đọc phải tự suy luận? Nếu PRD ngầm giả định "
            "điều gì đó (VD: không nói tới auth nhưng chắc chắn cần) mà "
            "không đánh dấu là giả định/out-of-scope, đó là finding.\n\n"
            "Với mỗi FR thiếu AC cụ thể, trích đúng FR-ID và câu văn mơ hồ "
            "trong finding."
        ),
    ),
    CriticLens(
        id="seam_and_downstream",
        name="Seam Reviewer (BA<->PRD) + Downstream Usability",
        system_prompt=(
            "Bạn có 2 nhiệm vụ trên bản PRD dưới đây, đối chiếu với phần "
            "NGỮ CẢNH (bản phân tích gốc của BA):\n\n"
            "1. SEAM BA<->PRD: Tìm chỗ PRD đi lệch, bỏ sót, hoặc diễn giải "
            "sai ý so với bản BA gốc — đây là điểm nối giữa 2 node trong "
            "pipeline, không phải khái niệm có sẵn trong BMAD, nhưng quan "
            "trọng với factory cụ thể này.\n"
            "2. DOWNSTREAM USABILITY (BMAD): Design/UX Designer sẽ đọc tiếp "
            "PRD này — thuật ngữ nghiệp vụ (tên entity, tên role...) có "
            "dùng NHẤT QUÁN xuyên suốt các FR không, hay đổi tên nửa chừng "
            "(VD: 'khách hàng' ở FR-001 nhưng 'người dùng' ở FR-005 khi rõ "
            "ràng là cùng 1 đối tượng)? ID của FR/NFR/BR có liên tục, không "
            "trùng, không có tham chiếu chéo bị đứt (VD: BR-002 nhắc tới "
            "FR-999 không tồn tại) không?\n\n"
            "Nếu PRD hoàn toàn nhất quán ở cả 2 khía cạnh, ghi VERDICT: ok."
        ),
    ),
]


def _thread_id_from_config(config: Optional[RunnableConfig]) -> str:
    if not config:
        return "default"
    return (config.get("configurable", {}) or {}).get("thread_id", "default")


def critic_prd(
    state: SoftwareFactoryState, config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    thread_id = _thread_id_from_config(config)

    summary = run_critic_pass(
        thread_id=thread_id,
        node_name=NODE_NAME,
        artifact_text=state.prd_v1,
        lenses=_LENSES,
        context=f"## BẢN PHÂN TÍCH GỐC CỦA BA\n\n{state.prd_draft}",
    )

    findings = classify_findings(summary)
    loop_iter = state.review_loop_iteration.get(NODE_NAME, 0)
    routing = decide_routing(findings, loop_iteration=loop_iter)

    updates: Dict[str, Any] = {
        "critic_reports": update_critic_reports(state.critic_reports, NODE_NAME, summary),
        "triage_action": update_triage_action(state.triage_action, NODE_NAME, routing["action"]),
    }

    if routing["action"] == "loop_upstream":
        # bad_spec: gốc vấn đề nằm ở input từ BA -> quay lại "ba", không
        # phải tự-loop trong "prd". Đây là backward-loop THẬT, khác với
        # route_gate_prd hiện tại (vốn chỉ quay lại đúng node prd).
        updates["review_loop_iteration"] = bump_review_loop_iteration(
            state.review_loop_iteration, NODE_NAME
        )
        updates["upstream_feedback"] = set_upstream_feedback(
            state.upstream_feedback,
            "ba",
            "Critic pass ở bước PRD phát hiện PRD không khớp / thiếu sót so "
            f"với bản phân tích BA gốc:\n{routing['feedback']}",
        )
    elif routing["action"] == "auto_patch":
        # patch: sửa tại chỗ trong phạm vi PRD, prd_node tự chạy lại với
        # feedback này (không cần quay lại BA).
        updates["upstream_feedback"] = set_upstream_feedback(
            state.upstream_feedback,
            "prd",
            f"Critic pass phát hiện cần sửa trực tiếp trong PRD:\n{routing['feedback']}",
        )
    elif routing["action"] == "halt_escalate":
        # intent_gap hoặc non-convergence: KHÔNG tự đoán, KHÔNG bỏ qua gate
        # — chỉ làm giàu payload hiển thị tại gate_prd để người quyết định
        # nhanh hơn, đúng tinh thần checkpoint-preview.md (surfacing, không
        # phải auto-decide).
        updates["pending_escalation_questions"] = "\n".join(
            f"- {q}" for q in routing.get("questions", [])
        )
    else:  # proceed — chỉ có defer/reject hoặc sạch hoàn toàn
        updates["review_loop_iteration"] = reset_review_loop_iteration(
            state.review_loop_iteration, NODE_NAME
        )
        updates["upstream_feedback"] = clear_upstream_feedback(
            state.upstream_feedback, "prd"
        )

    return updates


CRITIC_PRD = critic_prd
