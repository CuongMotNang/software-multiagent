"""Node UX — Sally, UX Designer: tạo UX Spec (user flows + danh sách màn
hình + edge case) từ PRD đã duyệt, TRƯỚC khi Architect vào việc.

Chỉ có nhánh simple (1 lệnh gọi LLM) — khác với ba/prd/design đã có sẵn
nhánh agentic để A/B test, node này mới thêm nên giữ đơn giản trước, có
thể bổ sung nhánh agentic sau khi đã chạy ổn với LLM thật.
"""
import os
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig

from graph.state import (
    SoftwareFactoryState,
    update_node_stats,
    push_content_history,
)
from graph.llm import llm_factory
from graph.repo_store import save_ux_spec, read_ux_spec
from graph.prompt_loader import load_prompt


def _get_feedback(state: SoftwareFactoryState) -> str:
    """Lấy phản hồi chỉnh sửa gần nhất cho UX Spec, gộp 2 nguồn:
    1. gate_history của gate_design — không có gate riêng cho ux_node, nên
       mượn lại gate_design để không mất phản hồi khi người reject/edit vì
       lý do liên quan UX.
    2. upstream_feedback['ux'] — critic_design phát hiện Design Document
       không khớp UX Spec (bad_spec) và tự quay lại 'ux', KHÔNG cần người
       bấm reject thủ công. Backward-loop thật, khác nguồn (1)."""
    parts = []

    if state.gate_history:
        design_gates = [h for h in state.gate_history if h.get("gate") == "gate_design"]
        if design_gates:
            last_gate = design_gates[-1]
            if last_gate.get("decision") in ["edit", "reject"]:
                note = last_gate.get("note", "")
                if note:
                    parts.append(f"[Từ người duyệt gate_design]\n{note}")

    critic_fb = state.upstream_feedback.get("ux", "")
    if critic_fb:
        parts.append(f"[Từ critic pass ở bước Design]\n{critic_fb}")

    return "\n\n".join(parts)


def ux_node(state: SoftwareFactoryState, config: RunnableConfig | None = None) -> Dict[str, Any]:
    """Node UX: prd_v1 (đã duyệt) -> ux_spec.

    Đứng giữa gate_prd (approve) và design trong graph — Winston (Architect)
    ở design_node sẽ đọc lại ux_spec.
    """
    thread_id = "default"
    if config:
        configurable = config.get("configurable", {}) or {}
        thread_id = configurable.get("thread_id", "default")

    prd = state.prd_approved.strip() or state.prd_v1.strip()
    if not prd:
        return {
            "ux_spec": "## LỖI: Không có PRD đã duyệt để thiết kế UX.",
            "status": "failed",
            "error": "prd_v1/prd_approved rỗng khi vào ux_node",
        }

    feedback = _get_feedback(state)

    provider_name = os.getenv("UX_PROVIDER", None)
    llm = llm_factory(provider_name)

    system_prompt = load_prompt("ux_system")
    user_prompt = f"## PRD ĐÃ DUYỆT\n\n{prd}\n\n"
    if feedback:
        user_prompt += (
            f"## LỊCH SỬ NHẬN XÉT TỪ REVIEWER (gate_design)\n"
            f"\"{feedback}\"\n\n"
            f"Lưu ý nhận xét trên khi cập nhật lại UX Spec — có thể nhận xét "
            f"nhắm vào phần thiết kế kỹ thuật chứ không phải UX, chỉ sửa nếu "
            f"thực sự liên quan tới UX."
        )
    else:
        user_prompt += "Hãy thiết kế UX Spec chi tiết dựa trên PRD trên."

    llm_response = llm.call(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.4,
        max_tokens=12000,
    )
    result = llm_response.content

    if result is None:
        return {
            "ux_spec": "## LỖI: LLM không trả về UX Spec.",
            "status": "failed",
            "error": "LLM returned None",
        }

    save_ux_spec(thread_id, result)

    node_stats = update_node_stats(
        state.node_stats, "ux",
        reject_count=0,
        tokens_used=llm_response.total_tokens,
        model=llm_response.model,
    )
    content_history = push_content_history(state.content_history, "ux", result)

    return {
        "ux_spec": result,
        "status": "running",
        "node_stats": node_stats,
        "content_history": content_history,
    }


# Alias để GraphBuilder dùng
UX_NODE = ux_node
