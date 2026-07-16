"""Node Debate BA — phòng họp point-to-point (Business-lite/Risk-lite/BA) chạy
TRƯỚC ba_node, dùng raw_requirements (input thô nhất trong cả pipeline) làm
chủ đề thảo luận.

Chỉ chạy khi meeting.needs_debate("ba") == True. "ba" đã được đánh dấu
evaluation-like=True trong meeting._EVALUATION_LIKE_NODES (khai thác yêu cầu
ban đầu — dễ bất đồng business vs feasibility) nên điều kiện A luôn đúng ->
debate luôn chạy cho stage này, giống hệt cơ chế của debate_prd.

Output: chỉ ghi debate_synthesis["ba"] — KHÔNG ghi đè raw_requirements.
ba_node sẽ tự đọc debate_synthesis khi build prompt (xem ba_node.py).
"""
from typing import Any, Dict, Optional

from langchain_core.runnables import RunnableConfig

from graph.state import SoftwareFactoryState, update_debate_synthesis
from graph.debate import DebatePersona, run_debate
from graph.meeting import needs_debate

NODE_NAME = "ba"

_PERSONAS = [
    DebatePersona(
        id="business",
        name="Business-lite",
        system_prompt=(
            "Bạn là Business-lite trong 1 buổi họp trước khi BA bắt tay phân "
            "tích yêu cầu. Vai trò của bạn: đại diện giá trị kinh doanh và "
            "mục tiêu thật của khách hàng — yêu cầu thô thường thiếu ngữ "
            "cảnh 'tại sao khách hàng cần cái này', hãy đặt câu hỏi/giả "
            "thuyết về mục tiêu nghiệp vụ đằng sau, và cảnh báo nếu thấy "
            "yêu cầu có vẻ đang giải quyết sai vấn đề. Phản biện thẳng, "
            "đừng chỉ gật đầu."
        ),
    ),
    DebatePersona(
        id="risk",
        name="Risk-lite",
        system_prompt=(
            "Bạn là Risk-lite trong 1 buổi họp trước khi BA bắt tay phân "
            "tích yêu cầu. Vai trò của bạn: soi rủi ro và tính khả thi SỚM — "
            "yêu cầu thô có phần nào không rõ ràng, mâu thuẫn nội tại, hoặc "
            "ẩn chứa giả định nguy hiểm (VD: giả định có sẵn hạ tầng/dữ liệu "
            "chưa chắc đã có) không? Nêu rõ, đừng để BA phải tự đoán."
        ),
    ),
    DebatePersona(
        id="ba",
        name="BA",
        is_lead=True,
        system_prompt=(
            "Bạn là Mary, Business Analyst, đồng thời là LEAD điều phối buổi "
            "họp. Vai trò của bạn: giữ đúng ý gốc khách hàng, cân bằng góc "
            "nhìn business và risk, và ở lượt cuối cùng bạn sẽ tổng hợp toàn "
            "bộ buổi họp thành 1 bản kết luận — nêu rõ: mục tiêu nghiệp vụ "
            "thật sự có thể là gì, những giả định/rủi ro cần điều tra thêm "
            "khi phân tích, và stakeholder nào không được bỏ sót. Đây là "
            "input bổ sung cho chính bạn khi viết prd_draft ngay sau đó, "
            "không phải bản phân tích cuối cùng."
        ),
    ),
]


def _thread_id_from_config(config: Optional[RunnableConfig]) -> str:
    if not config:
        return "default"
    return (config.get("configurable", {}) or {}).get("thread_id", "default")


def debate_ba(
    state: SoftwareFactoryState, config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    thread_id = _thread_id_from_config(config)

    topic = (
        "Chuẩn bị phân tích yêu cầu khách hàng dưới đây (bản thô, chưa qua "
        "xử lý gì). Thảo luận trước khi phân tích: mục tiêu nghiệp vụ thật "
        "sự có thể là gì, có giả định nguy hiểm nào ẩn trong yêu cầu không, "
        "stakeholder nào dễ bị bỏ sót?\n\n"
        f"## YÊU CẦU KHÁCH HÀNG (thô)\n\n{state.raw_requirements}"
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


DEBATE_BA = debate_ba


def should_debate_ba() -> bool:
    """Hàm điều kiện dùng trong graph_builder — tách riêng để dễ test/đọc.

    Static theo đúng thiết kế đã dùng cho should_debate_prd(): "ba" là
    evaluation-like -> điều kiện A luôn đúng -> luôn debate cho stage này.
    """
    return needs_debate("ba", altitude="feature", criticality_high=False)
