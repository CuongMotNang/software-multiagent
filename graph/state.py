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
    ux_spec: str = Field(
        "", description=(
            "Đặc tả UX từ Sally (UX Designer): user flows, danh sách màn hình "
            "kèm lý do UX, tương tác/trạng thái edge-case. Input BẮT BUỘC cho "
            "design_node — Winston (Architect) dùng lại danh sách màn hình ở "
            "đây thay vì tự nghĩ ra, không thay thế vai trò Architect."
        )
    )
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

    tech_docs: str = Field(
        "", description=(
            "Tài liệu handoff (README) do Paige (Technical Writer) tổng hợp "
            "cuối pipeline từ PRD + Design + UX + code đã sinh — cho người "
            "đọc sau (dev khác, stakeholder), KHÔNG phải input cho node nào "
            "khác trong graph."
        )
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

    # === Critic pass / Triage (BMAD-inspired, xem docs/architecture-bmad.md) ===
    critic_reports: dict[str, dict] = Field(
        default_factory=dict,
        description=(
            "Theo node -> {lens_id: {verdict, findings: [...], report_path}}. "
            "Mỗi lens là 1 subagent review độc lập (không chia sẻ context), "
            "full report ghi ra file qua repo_store, chỉ tóm tắt lưu ở đây."
        ),
    )
    triage_action: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Theo node -> hành động triage gần nhất: "
            "'proceed' | 'auto_patch' | 'loop_upstream' | 'halt_escalate'."
        ),
    )
    review_loop_iteration: dict[str, int] = Field(
        default_factory=dict,
        description=(
            "Theo node -> số vòng lặp bad_spec-loopback đã chạy (non-convergence "
            "guard). Vượt ngưỡng MAX_REVIEW_LOOP_ITERATIONS thì bắt buộc "
            "halt_escalate thay vì lặp lại vô hạn."
        ),
    )
    upstream_feedback: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Theo TÊN NODE ĐÍCH -> nội dung feedback cần xử lý ở lượt chạy kế "
            "tiếp của node đó. Dùng cho backward-loop thật (vd critic ở PRD "
            "phát hiện bad_spec do lỗi từ BA -> ghi vào upstream_feedback['ba'], "
            "khác với gate_history vốn chỉ gắn với đúng 1 gate)."
        ),
    )
    debate_synthesis: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Theo node -> bản tổng hợp (do lead viết) từ phòng họp debate "
            "point-to-point trước khi producer node chạy. Transcript đầy đủ "
            "KHÔNG lưu ở đây (đã ghi ra file qua repo_store) — chỉ giữ bản "
            "tổng hợp gọn, đúng nguyên tắc context isolation."
        ),
    )
    pending_escalation_questions: str = Field(
        "",
        description=(
            "Câu hỏi cụ thể cần người quyết định khi triage trả về "
            "'halt_escalate' (intent_gap hoặc non-convergence). Gate vẫn luôn "
            "chờ người như bình thường — trường này chỉ làm giàu payload hiển "
            "thị tại gate, không tạo thêm gate mới, không tự động bỏ qua người."
        ),
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


# Ngưỡng non-convergence guard cho backward-loop (bad_spec). Import lại từ
# triage.py — trước đây định nghĩa trùng ở cả 2 nơi (rủi ro lệch mặc định
# nếu sửa 1 chỗ quên chỗ kia), giờ chỉ 1 nguồn duy nhất.
from graph.triage import MAX_REVIEW_LOOP_ITERATIONS  # noqa: E402


def update_critic_reports(
    reports: dict[str, dict], node_name: str, summary: dict
) -> dict[str, dict]:
    """BẢN SAO MỚI của critic_reports với entry của node_name được ghi đè
    bằng summary mới nhất (mỗi node chỉ cần giữ lượt gần nhất, lịch sử đầy đủ
    đã nằm trong file report do repo_store lưu)."""
    all_reports = dict(reports)
    all_reports[node_name] = summary
    return all_reports


def update_triage_action(
    actions: dict[str, str], node_name: str, action: str
) -> dict[str, str]:
    all_actions = dict(actions)
    all_actions[node_name] = action
    return all_actions


def bump_review_loop_iteration(
    iterations: dict[str, int], node_name: str
) -> dict[str, int]:
    """Tăng bộ đếm vòng lặp bad_spec-loopback của node_name lên 1."""
    all_iter = dict(iterations)
    all_iter[node_name] = all_iter.get(node_name, 0) + 1
    return all_iter


def reset_review_loop_iteration(
    iterations: dict[str, int], node_name: str
) -> dict[str, int]:
    """Reset bộ đếm về 0 khi node_name đã proceed sạch qua gate."""
    all_iter = dict(iterations)
    all_iter[node_name] = 0
    return all_iter


def update_debate_synthesis(
    synthesis: dict[str, str], node_name: str, content: str
) -> dict[str, str]:
    all_synthesis = dict(synthesis)
    all_synthesis[node_name] = content
    return all_synthesis


def set_upstream_feedback(
    feedback: dict[str, str], target_node: str, content: str
) -> dict[str, str]:
    """BẢN SAO MỚI của upstream_feedback, ghi feedback cần xử lý cho
    target_node ở lượt chạy kế tiếp (backward-loop thật, không phải self-loop)."""
    all_fb = dict(feedback)
    all_fb[target_node] = content
    return all_fb


def clear_upstream_feedback(
    feedback: dict[str, str], target_node: str
) -> dict[str, str]:
    all_fb = dict(feedback)
    all_fb.pop(target_node, None)
    return all_fb