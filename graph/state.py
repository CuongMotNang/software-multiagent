"""SoftwareFactory State — Pydantic model cho toàn bộ pipeline."""
import os
from datetime import datetime                              # ← MỚI
import operator
from typing import Annotated, Literal, Optional                         # ← sửa
from pydantic import BaseModel, Field

# Số phiên bản nội dung gần nhất giữ lại trong content_history, cấu hình
# qua .env (MAX_HISTORY_VERSIONS=5 mặc định).
MAX_HISTORY_VERSIONS = int(os.getenv("MAX_HISTORY_VERSIONS", "5"))


class SoftwareFactoryState(BaseModel):
    """State xuyên suốt pipeline từ yêu cầu → code → deploy."""

    # === Input ===
    raw_requirements: str = Field(
        "", description="Yêu cầu thô từ khách hàng"
    )

    # === Phase 1: Analysis ===
    prd_draft: str = Field(
        "", description="Bản phân tích BA (Use cases, Actors, Flow)"
    )
    prd_v1: str = Field(
        "", description="PRD hoàn chỉnh từ Product Manager"
    )
    prd_approved: str = Field(
        "", description="PRD đã được phê duyệt qua HITL Gate #1"
    )

    # === Phase 2: Design ===
    design_doc: str = Field(
        "", description="Thiết kế kỹ thuật (DB schema, API, cấu trúc)"
    )
    design_tokens: str = Field(
        "", description="Design tokens JSON (colors/spacing/typography/components) — Giai đoạn 3.1, dùng làm ngữ cảnh bắt buộc khi ui_node sinh screen"
    )
    mockup_html: str = Field(
        "", description="HTML mockup UI (1 file, CSS inline)"
    )
    mockup_screens: dict[str, str] = Field(
        default_factory=dict,
        description="Dict các màn hình mockup: {tên_file: nội_dung_HTML}"
    )
    mockup_screenshots: list[str] = Field(
        default_factory=list,
        description="Đường dẫn ảnh screenshot từng màn hình của mockup (Playwright capture)"
    )
    mockup_feedback: str = Field(
        "", description="Feedback từ khách hàng về mockup"
    )

    # === Phase 3: Code ===
    repo_path: str = Field(
        "", description="Đường dẫn sandbox chứa code đã generate"
    )
    engineer_log: str = Field(
        "", description="Truncated log từ OpenHands JSONL output (few thousand chars)"
    )
    code_diff: str = Field(
        "", description="Diff của code đã thay đổi"
    )
    test_results: str = Field(
        "", description="Log thô kết quả chạy test (passed/failed)"
    )
    test_report: dict = Field(                             # đổi str -> dict
        default_factory=dict,
        description="Báo cáo test có cấu trúc: {coverage_percent, bugs, recommendations}"
    )

    # === Phase 4: Deploy ===
    preview_url: str = Field(
        "", description="URL preview đã deploy (Vercel/Netlify)"
    )
    preview_expiry: datetime | None = Field(                 # đổi str -> datetime
        None, description="Thời điểm preview link hết hạn"
    )

    # === HITL Control ===
    current_gate: Literal[
        "gate_prd", "gate_design", "gate_mockup",
        "gate_code_review", "gate_test_result",
        "gate_deploy_confirm", "gate_business_signoff", ""
    ] = Field("", description="Gate đang chờ duyệt")
    gate_decision: Literal["approve", "edit", "reject", "approve_with_edit"] | None = Field(
        None, description="Quyết định cho gate hiện tại (approve / edit / reject / approve_with_edit)"
    )
    gate_history: Annotated[list[dict], operator.add] = Field(
        default_factory=list,
        description="Lịch sử mọi gate đã qua: [{gate, role, decision, note, timestamp}]"
    )
    is_escalation: bool = Field(
        default=False,
        description="Đánh dấu thread đang escalate lên Dev do auto-retry test thất bại ≥3 lần"
    )

    # === Observability (Task 1) ===
    node_stats: dict[str, dict] = Field(
        default_factory=dict,
        description="Theo node -> {reject_count, tokens_used, model}"
    )
    content_history: dict[str, list[dict]] = Field(
        default_factory=dict,
        description="Theo node -> N bản gần nhất [{content, timestamp}], N=MAX_HISTORY_VERSIONS"
    )

    # === Metadata ===
    thread_id: str = Field(
        "", description="Thread ID cho LangGraph checkpoint"
    )
    status: str = Field(
        "created", description="created | running | paused | completed | failed"
    )
    error: str = Field(
        "", description="Lỗi nếu có"
    )


# ---------------------------------------------------------------------------
# Helpers cho node_stats / content_history — dùng chung trong mọi node.
#
# QUAN TRỌNG: node_stats và content_history là dict, LangGraph KHÔNG tự
# deep-merge dict giữa các lần node trả `updates` (không giống gate_history
# dùng operator.add cho list). Nếu 1 node chỉ trả updates["node_stats"] =
# {"prd": {...}} thôi, nó sẽ GHI ĐÈ toàn bộ field, XOÁ MẤT dữ liệu của các
# node khác (vd "ba") đã ghi trước đó. Vì vậy PHẢI luôn copy toàn bộ dict
# hiện tại rồi mới sửa đúng key của node mình — 2 hàm dưới đây làm sẵn việc
# đó, các node chỉ cần gọi, không tự viết lại logic copy.
# ---------------------------------------------------------------------------

def count_rejects(gate_history: list[dict], gate_name: str) -> int:
    """Đếm số lần bị reject ở 1 gate cụ thể, dựa trên gate_history có sẵn.
    Không lưu counter riêng để tránh 2 nguồn sự thật lệch nhau.
    """
    return sum(
        1 for h in gate_history
        if h.get("gate") == gate_name and h.get("decision") == "reject"
    )


def update_node_stats(
    stats: dict[str, dict],
    node_name: str,
    *,
    reject_count: int,
    tokens_used: int,
    model: str,
) -> dict[str, dict]:
    """Trả về BẢN SAO MỚI của node_stats với entry của node_name được cập
    nhật (cộng dồn tokens_used, ghi đè model/reject_count mới nhất).
    KHÔNG mutate `stats` gốc.
    """
    all_stats = dict(stats)
    prev = all_stats.get(node_name, {})
    all_stats[node_name] = {
        "reject_count": reject_count,
        "tokens_used": prev.get("tokens_used", 0) + tokens_used,
        "model": model,
    }
    return all_stats


def push_content_history(
    history: dict[str, list[dict]], node_name: str, content: str
) -> dict[str, list[dict]]:
    """Trả về BẢN SAO MỚI của content_history với 1 bản ghi mới (mới nhất
    ở đầu list) cho node_name, cắt còn tối đa MAX_HISTORY_VERSIONS bản.
    KHÔNG mutate `history` gốc.
    """
    all_history = dict(history)
    node_hist = list(all_history.get(node_name, []))
    node_hist.insert(0, {"content": content, "timestamp": datetime.now().isoformat()})
    all_history[node_name] = node_hist[:MAX_HISTORY_VERSIONS]
    return all_history