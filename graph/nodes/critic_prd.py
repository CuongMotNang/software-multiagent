"""Node Critic PRD — parallel critic pass + triage cho prd_v1.

Chạy SAU prd_node, TRƯỚC gate_prd. Không thay thế gate người — chỉ làm
giàu chất lượng trước khi tới gate, và quyết định có cần quay lại BA
(bad_spec), tự sửa tại chỗ (patch), hay phải dừng hỏi người (intent_gap)
trước khi trình gate_prd như bình thường.
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
        id="feasibility",
        name="Feasibility Critic",
        system_prompt=(
            "Bạn là Feasibility Critic trong một software factory nhỏ. Đọc "
            "bản PRD dưới đây và chỉ ra những yêu cầu KHÔNG khả thi về mặt "
            "kỹ thuật, thời gian, hoặc nguồn lực trong bối cảnh 1 đội nhỏ. "
            "Chỉ nêu vấn đề có bằng chứng cụ thể trong văn bản, không suy "
            "đoán những gì PRD không nói tới."
        ),
    ),
    CriticLens(
        id="edge_case",
        name="Edge Case / Risk Critic",
        system_prompt=(
            "Bạn là Edge Case & Risk Critic. Đọc bản PRD dưới đây, tìm các "
            "tình huống biên (edge case), luồng lỗi, hoặc rủi ro nghiệp vụ "
            "quan trọng chưa được đề cập tới. Chỉ nêu vấn đề cụ thể, không "
            "lặp lại nội dung đã có sẵn trong PRD."
        ),
    ),
    CriticLens(
        id="seam_with_ba",
        name="Seam Reviewer (BA <-> PRD)",
        system_prompt=(
            "Bạn là Seam Reviewer, chuyên soi điểm nối giữa bản phân tích "
            "gốc của BA (đưa trong phần NGỮ CẢNH) và bản PRD hoàn chỉnh "
            "(đưa trong phần NỘI DUNG CẦN REVIEW). Tìm chỗ PRD đi lệch, bỏ "
            "sót, hoặc diễn giải sai ý so với bản BA gốc. Nếu PRD hoàn toàn "
            "nhất quán với BA, ghi VERDICT: ok."
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
