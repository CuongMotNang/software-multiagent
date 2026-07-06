"""SoftwareFactory State — Pydantic model cho toàn bộ pipeline."""
import os
from datetime import datetime                              # ← MỚI
import operator
from typing import Annotated, Literal, Optional                         # ← sửa
from pydantic import BaseModel, Field


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
    pending_gate_role: Literal["ba", "dev", "test", ""] = Field(
        "", description="Vai trò cần phê duyệt: ba | dev | test"
    )
    gate_decision: Literal["approve", "edit", "reject"] | None = Field(
        None, description="Quyết định cho gate hiện tại"
    )
    gate_history: Annotated[list[dict], operator.add] = Field(
        default_factory=list,
        description="Lịch sử mọi gate đã qua: [{gate, role, decision, note, timestamp}]"
    )
    is_escalation: bool = Field(
        default=False,
        description="Đánh dấu thread đang escalate lên Dev do auto-retry test thất bại ≥3 lần"
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
    # --- Observability ---
    node_stats: dict[str, dict] = Field(
        default_factory=dict,
        description="Theo node -> {reject_count, tokens_used, model}"
    )
    content_history: dict[str, list[dict]] = Field(
        default_factory=dict,
        description="Theo node -> list N bản gần nhất [{content, timestamp}]"
    )
