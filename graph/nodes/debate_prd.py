"""Node Debate PRD — phòng họp point-to-point (PM/Architect-lite/Risk-BA-liaison)
chạy TRƯỚC prd_node, dùng bản phân tích của BA làm chủ đề thảo luận.

Chỉ chạy khi meeting.needs_debate("prd") == True. Hiện tại altitude/
criticality_high chưa có nguồn dữ liệu thật trong state (đã thống nhất: để
tĩnh, không chặn việc build) — dùng default "feature"/False. Vì "prd" đã
được đánh dấu evaluation-like=True trong meeting._EVALUATION_LIKE_NODES nên
điều kiện A luôn đúng -> debate luôn chạy cho stage này, bất kể altitude.

Output: chỉ ghi debate_synthesis["prd"] — KHÔNG ghi đè prd_draft/prd_v1.
prd_node sẽ tự đọc debate_synthesis khi build prompt (xem prd_node.py).
"""
from typing import Any, Dict, Optional

from langchain_core.runnables import RunnableConfig

from graph.state import SoftwareFactoryState, update_debate_synthesis
from graph.debate import DebatePersona, run_debate
from graph.meeting import needs_debate

NODE_NAME = "prd"

_PERSONAS = [
    DebatePersona(
        id="architect",
        name="Architect-lite",
        system_prompt=(
            "Bạn là Architect-lite trong 1 buổi họp trước khi viết PRD. Vai "
            "trò của bạn: soi tính khả thi kỹ thuật SỚM, trước khi PM chốt "
            "PRD. Nêu rõ nếu có yêu cầu nào khó làm trong bối cảnh 1 đội nhỏ, "
            "hoặc cần đánh đổi (trade-off) mà PM/BA có thể chưa lường tới. "
            "Phản biện thẳng nếu thấy ý kiến trước đó chưa ổn, đừng chỉ gật đầu."
        ),
    ),
    DebatePersona(
        id="risk",
        name="Risk/BA-liaison",
        system_prompt=(
            "Bạn là Risk & BA-liaison trong 1 buổi họp trước khi viết PRD. "
            "Vai trò của bạn: giữ đúng ý gốc của khách hàng (bản phân tích "
            "BA), chỉ ra nếu ý kiến của người khác trong phòng đang làm lệch "
            "ý gốc, và nêu rủi ro nghiệp vụ/edge-case bị bỏ sót. Phản biện "
            "thẳng, không nhượng bộ chỉ để đồng thuận cho nhanh."
        ),
    ),
    DebatePersona(
        id="pm",
        name="PM",
        is_lead=True,
        system_prompt=(
            "Bạn là PM, đồng thời là LEAD điều phối buổi họp. Vai trò của "
            "bạn: đại diện giá trị kinh doanh, cân bằng giữa các ý kiến, và "
            "ở lượt cuối cùng bạn sẽ tổng hợp toàn bộ buổi họp thành 1 bản "
            "kết luận. Trong lúc thảo luận, đưa quan điểm business rõ ràng, "
            "không né tránh bất đồng."
        ),
    ),
]


def _thread_id_from_config(config: Optional[RunnableConfig]) -> str:
    if not config:
        return "default"
    return (config.get("configurable", {}) or {}).get("thread_id", "default")


def debate_prd(
    state: SoftwareFactoryState, config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    thread_id = _thread_id_from_config(config)

    topic = (
        "Chuẩn bị viết PRD hoàn chỉnh từ bản phân tích BA dưới đây. Thảo "
        "luận trước khi viết: có gì cần làm rõ/đổi hướng/bổ sung không?\n\n"
        f"## BẢN PHÂN TÍCH BA\n\n{state.prd_draft}"
    )

    synthesis = run_debate(
        thread_id=thread_id,
        node_name=NODE_NAME,
        topic=topic,
        personas=_PERSONAS,
    )

    return {
        "debate_synthesis": update_debate_synthesis(
            state.debate_synthesis, NODE_NAME, synthesis
        ),
    }


DEBATE_PRD = debate_prd


def should_debate_prd() -> bool:
    """Hàm điều kiện dùng trong graph_builder — tách riêng để dễ test/đọc.

    Static theo thiết kế đã thống nhất: altitude="feature", criticality
    thấp -> điều kiện B sai, nhưng điều kiện A ("prd" là evaluation-like)
    luôn đúng -> luôn debate cho stage này.
    """
    return needs_debate("prd", altitude="feature", criticality_high=False)
