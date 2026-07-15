"""Meeting — quyết định khi nào cần agent-team debate thật (nhiều instance
tranh luận với nhau), thay vì 1 agent tự làm.

Chỉ dùng đúng 2 tiêu chí đã verify trực tiếp trong repo BMAD-METHOD:

1) core-skills/bmad-party-mode/references/mode-auto.md — spawn agent thật
   khi: "a genuine evaluation, review, or critique... that fails if one
   mind voices every side and they drift into agreement" HOẶC "the personas
   would plausibly reach different conclusions, and that divergence is the
   point". Mặc định là "voice inline" (1 agent) — spawn debate là ngoại lệ.

2) bmm-skills/3-solutioning/bmad-architecture/references/reviewer-gate.md —
   scale độ nặng theo "altitude" (initiative > feature > epic) và
   criticality (regulated/khó đảo ngược).

KHÔNG có tier "auto-approve/skip gate" nào ở đây — hàm dưới chỉ quyết định
CÓ CẦN DEBATE THẬT TRƯỚC GATE hay không, gate người vẫn luôn diễn ra sau đó.
"""
from __future__ import annotations

from typing import Literal

Altitude = Literal["initiative", "feature", "epic"]

# Điều kiện A (mode-auto.md): node nào về bản chất là "đánh giá/phản biện"
# nơi các vai trò dễ bất đồng thật sự (business vs feasibility vs risk...).
# Đây là nhận định thủ công ban đầu — nên rà soát lại định kỳ theo dữ liệu
# thực tế (xem mục "tự học/tinh chỉnh" trong tài liệu kiến trúc).
_EVALUATION_LIKE_NODES = {
    "ba": True,          # khai thác yêu cầu ban đầu — dễ bất đồng business vs feasibility
    "prd": True,         # PRD định hình downstream — nên coi là evaluation-like
    "design": True,      # architecture — seam cross-team, dễ bất đồng kỹ thuật
    "ui": False,         # chỉnh UI thường không có "góc nhìn đối lập" thật sự
    "engineer": False,   # code-gen không phải evaluation; nhưng code REVIEW thì có
    "code_review": True,
}


def needs_debate(
    node_name: str,
    altitude: Altitude = "feature",
    criticality_high: bool = False,
) -> bool:
    """True nếu nên escalate lên agent-team debate thật trước khi trình gate.

    node_name: tên node đang xét (khớp key trong _EVALUATION_LIKE_NODES)
    altitude: phạm vi ảnh hưởng của artifact — "initiative" = ảnh hưởng toàn
        bộ sản phẩm/nhiều team, "feature" = 1 tính năng, "epic" = 1 story nhỏ
    criticality_high: True nếu thuộc diện khó đảo ngược / quy định / bảo mật

    Điều kiện A HOẶC B đúng -> debate thật. Cả hai sai -> 1 agent làm, gate
    vẫn có nhưng nhẹ (không tốn thêm subagent).
    """
    condition_a = _EVALUATION_LIKE_NODES.get(node_name, False)
    condition_b = altitude == "initiative" or criticality_high
    return condition_a or condition_b
