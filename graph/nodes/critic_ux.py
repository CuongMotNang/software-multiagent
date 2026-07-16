"""Node Critic UX — parallel critic pass cho ux_spec, chạy SAU ux_node,
TRƯỚC design_node.

Khác critic_prd/critic_design (không dùng triage 5 nhóm đầy đủ) — vì
ux_spec KHÔNG có 1 "node trước" tự nhiên để loop_upstream về (upstream của
UX chỉ là prd_v1, vốn đã qua critic_prd riêng). Nên critic_ux dùng verdict
đơn giản: "ok" -> đi tiếp design; bất kỳ lens nào "concerns" -> loop lại
CHÍNH ux_node để tự sửa (không đụng tới ba/prd), có giới hạn số vòng lặp
(reuse review_loop_iteration + MAX_REVIEW_LOOP_ITERATIONS y hệt cơ chế
non-convergence guard đã verify từ BMAD-METHOD step-04-review.md).

2 lens lấy từ bmm-skills/2-plan-workflows/bmad-ux/references/validate.md
(đã verify trực tiếp) — bỏ "token completeness" vì tokens (design_tokens)
CHƯA được sinh ở giai đoạn này (chạy sau design, không phải trước).
"""
from typing import Any, Dict, Optional

from langchain_core.runnables import RunnableConfig

from graph.state import (
    SoftwareFactoryState,
    update_critic_reports,
    bump_review_loop_iteration,
    reset_review_loop_iteration,
    set_upstream_feedback,
    clear_upstream_feedback,
)
from graph.critic import CriticLens, run_critic_pass
from graph.triage import MAX_REVIEW_LOOP_ITERATIONS

NODE_NAME = "ux"

_LENSES = [
    CriticLens(
        id="flow_coverage",
        name="Flow Coverage Critic",
        system_prompt=(
            "Bạn là Flow Coverage Critic cho UX Spec dưới đây. Đối chiếu "
            "với PRD (phần NGỮ CẢNH): mọi user role trong PRD có ít nhất 1 "
            "user flow trong UX Spec không? Mọi FR (functional requirement) "
            "trong PRD có được 1 màn hình nào đó trong UX Spec phục vụ "
            "không, hay có FR bị bỏ sót hoàn toàn? Nếu đầy đủ, ghi VERDICT: "
            "ok. Chỉ nêu finding có bằng chứng cụ thể (trích FR-ID/role bị "
            "thiếu), không suy đoán."
        ),
    ),
    CriticLens(
        id="component_state_coverage",
        name="Component & State Coverage Critic",
        system_prompt=(
            "Bạn là Component & State Coverage Critic cho UX Spec dưới đây. "
            "Với mỗi màn hình có rủi ro UX cao (form nhập liệu, luồng thanh "
            "toán, xoá dữ liệu, danh sách có thể rỗng...): UX Spec có thiết "
            "kế đủ trạng thái loading/empty/error/success chưa? Danh sách "
            "màn hình (mục 2) có màn hình nào thừa — không phục vụ nhu cầu "
            "user cụ thể nào — mà lẽ ra nên bỏ? Nếu đầy đủ và không có màn "
            "hình thừa, ghi VERDICT: ok."
        ),
    ),
]


def _thread_id_from_config(config: Optional[RunnableConfig]) -> str:
    if not config:
        return "default"
    return (config.get("configurable", {}) or {}).get("thread_id", "default")


def critic_ux(
    state: SoftwareFactoryState, config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    thread_id = _thread_id_from_config(config)

    summary = run_critic_pass(
        thread_id=thread_id,
        node_name=NODE_NAME,
        artifact_text=state.ux_spec,
        lenses=_LENSES,
        context=f"## PRD ĐÃ DUYỆT\n\n{state.prd_approved or state.prd_v1}",
    )

    has_concerns = any(
        r.get("verdict") != "ok" for r in summary.values()
    )
    loop_iter = state.review_loop_iteration.get(NODE_NAME, 0)

    updates: Dict[str, Any] = {
        "critic_reports": update_critic_reports(state.critic_reports, NODE_NAME, summary),
    }

    if has_concerns and loop_iter < MAX_REVIEW_LOOP_ITERATIONS:
        # Loop lại chính ux_node — không phải backward-loop lên prd/ba, vì
        # đây là vấn đề chất lượng CỦA ux_spec, không phải input không rõ.
        feedback_lines = []
        for lens_id, r in summary.items():
            if r.get("verdict") != "ok":
                feedback_lines.extend(r.get("findings", []))
        updates["review_loop_iteration"] = bump_review_loop_iteration(
            state.review_loop_iteration, NODE_NAME
        )
        updates["upstream_feedback"] = set_upstream_feedback(
            state.upstream_feedback,
            "ux",
            "Critic pass phát hiện UX Spec cần sửa:\n" + "\n".join(f"- {f}" for f in feedback_lines),
        )
    else:
        # ok, hoặc đã hết ngưỡng vòng lặp (non-convergence guard) -> đi
        # tiếp design, không kẹt vô hạn dù còn concerns nhỏ.
        updates["review_loop_iteration"] = reset_review_loop_iteration(
            state.review_loop_iteration, NODE_NAME
        )
        updates["upstream_feedback"] = clear_upstream_feedback(
            state.upstream_feedback, "ux"
        )

    return updates


CRITIC_UX = critic_ux


def route_critic_ux(state: SoftwareFactoryState) -> str:
    """loop lại "ux" nếu còn upstream_feedback['ux'] mới ghi (concerns +
    chưa hết ngưỡng), ngược lại đi tiếp "design"."""
    fb = state.get("upstream_feedback", {}).get("ux") if isinstance(state, dict) \
        else state.upstream_feedback.get("ux")
    return "ux" if fb else "design"
