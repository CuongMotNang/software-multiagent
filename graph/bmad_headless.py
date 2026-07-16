"""BMAD headless helper — cài _bmad/ vào workspace 1 lần, parse kết quả
headless từ output của agent runtime.

QUAN TRỌNG — đọc trước khi dùng: BMAD-METHOD chỉ có headless.md (schema JSON
chính thức: status complete/partial/blocked + assumptions[]/open_questions[])
cho 4 skill: bmad-brainstorming, bmad-ux, bmad-prd, bmad-architecture (đã
verify trực tiếp, không có ở bmad-quick-dev/bmad-dev-auto/bmad-agent-dev).

Với pha Implementation (bmad-dev-auto), BMAD có sẵn cơ chế HALT/blocked
NATIVE (step-01-clarify-and-route.md: "HALT with status blocked and
blocking condition ...") và chấp nhận invocation prompt tự do làm intent
bootstrap (không bắt buộc phải có sẵn stories.yaml) — đây LÀ hành vi thật
đã verify. Nhưng bmad-dev-auto không tự trả JSON có cấu trúc cho pipeline
Python đọc — nó giao tiếp qua transcript tự do + trạng thái ghi trong file
spec trên đĩa. Nên với engineer_node, hàm parse dưới đây dùng 1 QUY ƯỚC BỔ
SUNG của riêng pipeline này (không phải chuẩn BMAD): yêu cầu agent kết thúc
bằng 1 dòng JSON cuối cùng theo đúng field-name của headless-schemas.md để
tái dùng chung 1 parser cho mọi skill — đây là phần TỰ THÊM, ghi rõ ở đây để
không nhầm là hành vi built-in của BMAD.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Optional, TypedDict


class BmadHeadlessResult(TypedDict):
    status: str  # "complete" | "partial" | "blocked" | "unknown"
    summary: str
    assumptions: list[str]
    open_questions: list[str]
    raw_output: str


_JSON_TAIL_RE = re.compile(r"\{[^{}]*\"status\"\s*:\s*\"(?:complete|partial|blocked)\"[^{}]*\}")


def ensure_bmad_installed(
    workspace_path: Path, tools: str = "opencode", timeout_s: int = 180
) -> tuple[bool, str]:
    """Cài `_bmad/` vào workspace nếu chưa có. Idempotent — nếu đã có
    `_bmad/` thì bỏ qua, không cài lại (npx bmad-method install khá nặng,
    không nên chạy lại mỗi lần gọi node).

    Trả (ok, message). ok=False không phải lỗi khiến pipeline phải dừng —
    caller tự quyết định fallback (VD: rơi về nhánh OpenCode custom-prompt
    cũ) thay vì để cả node fail cứng.
    """
    workspace_path.mkdir(parents=True, exist_ok=True)
    bmad_dir = workspace_path / "_bmad"
    if bmad_dir.exists():
        return True, "_bmad/ đã có sẵn, bỏ qua cài lại"

    try:
        proc = subprocess.run(
            [
                "npx", "-y", "bmad-method", "install",
                "--directory", str(workspace_path),
                "--modules", "bmm",
                "--tools", tools,
                "--yes",
            ],
            cwd=str(workspace_path),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except FileNotFoundError:
        return False, "Không tìm thấy lệnh 'npx' — cần cài Node.js trên máy chạy engineer_node"
    except subprocess.TimeoutExpired:
        return False, f"Cài _bmad/ timeout sau {timeout_s}s"

    if proc.returncode != 0:
        return False, f"npx bmad-method install thất bại: {proc.stderr[-2000:]}"
    return True, "Cài _bmad/ thành công"


def build_headless_prompt(skill_name: str, intent: str, extra_rule: str = "") -> str:
    """Ghép prompt gọi 1 skill BMAD ở chế độ headless — theo đúng convention
    của headless.md thật (chỉ có ở bmad-prd/ux/architecture/brainstorming):
    intent tự do trong tin nhắn đầu, không được hỏi lại, thiếu thì tự suy
    đoán vào assumptions[] hoặc dừng ở open_questions[] + status: partial.

    Với skill KHÔNG có headless.md thật (VD bmad-dev-auto dùng cho
    engineer_node) — vẫn dùng đúng khuôn này nhưng đó là quy ước TỰ THÊM của
    pipeline (xem docstring module), không phải hành vi built-in.

    LƯU Ý: hàm này tự áp 1 schema JSON cứng (status/summary/assumptions/
    open_questions) — chỉ dùng cho skill KHÔNG có headless.md thật. Với
    prd/ux/architecture (CÓ headless.md + assets/headless-schemas.md riêng,
    schema khác nhau giữa 3 skill — xem build_real_headless_prompt bên dưới.
    """
    return f"""{skill_name}

## INTENT (chế độ headless — không được hỏi lại người dùng)
{intent}

## QUY TẮC BẮT BUỘC
- KHÔNG hỏi lại, KHÔNG dừng chờ trả lời. Nếu thiếu thông tin, tự suy đoán
  hợp lý và ghi vào assumptions[]; chỉ khi thực sự không đủ để tiếp tục thì
  dừng với status "partial" kèm open_questions[] cụ thể.
- {extra_rule if extra_rule else "Hoàn thành trọn vẹn nếu đủ thông tin."}
- BẮT BUỘC kết thúc phản hồi bằng ĐÚNG 1 dòng JSON cuối cùng (không kèm
  markdown code fence, không có chữ nào sau đó), format:
  {{"status": "complete"|"partial"|"blocked", "summary": "...", "assumptions": [...], "open_questions": [...]}}
"""


def build_real_headless_prompt(
    skill_name: str,
    intent_type: str,
    payload_lines: str,
    extra_rule: str = "",
) -> str:
    """Gọi 1 skill CÓ headless.md thật (bmad-prd/bmad-ux/bmad-architecture)
    theo đúng cách BMAD tự định nghĩa — KHÔNG tự áp schema JSON ở đây (khác
    build_headless_prompt() ở trên), vì mỗi skill có schema riêng, khác
    nhau (VD bmad-prd trả field "prd", bmad-ux trả "design"+"experience",
    bmad-architecture trả "spine") — để agent tự đọc đúng file
    `references/headless.md` + `assets/headless-schemas.md` của CHÍNH skill
    đó (đã có sẵn trong _bmad/ do ensure_bmad_installed() cài) và tuân theo,
    tránh lệch schema do mình tự chép lại sai.

    intent_type: "create" | "update" | "validate" — field `intent` mà
    headless.md của 3 skill này đều yêu cầu ở input.
    payload_lines: nội dung cụ thể (PRD, UX Spec, brief...) tương ứng với
    intent_type, do caller tự soạn theo đúng "Inputs" section trong
    headless.md của skill đó (khác nhau giữa create/update/validate).
    """
    return f"""{skill_name}

## HEADLESS MODE — bắt buộc
headless: true
intent: {intent_type}

Đây là lời gọi headless thật (không có người tương tác) — hãy đọc và tuân
theo ĐÚNG file `references/headless.md` của chính skill `{skill_name}` này
(đã có sẵn trong thư mục _bmad/ hiện tại) cho toàn bộ lượt chạy: không hỏi
lại, không chào hỏi, tự suy đoán và ghi vào assumptions[] những gì không
được xác nhận trực tiếp, dừng ở open_questions[] những gì cần người quyết
định. Kết thúc bằng ĐÚNG 1 dòng JSON cuối cùng, khớp CHÍNH XÁC schema trong
`assets/headless-schemas.md` của skill này ứng với intent "{intent_type}"
(không kèm markdown code fence, không có chữ nào sau JSON).

## PAYLOAD
{payload_lines}

{extra_rule}
"""


def parse_generic_json_tail(raw_output: str) -> dict:
    """Parser TỔNG QUÁT — không ép về 1 TypedDict cố định như
    parse_headless_result() (vốn chỉ đúng cho schema tự chế của
    bmad-dev-auto). Dùng cho prd/ux/architecture vì mỗi skill trả field
    khác nhau (prd / design+experience / spine).

    Trả về dict thô parse được (luôn có ít nhất key "status" nếu tìm thấy
    JSON hợp lệ, "unknown" nếu không tìm thấy gì) — caller tự đọc field
    riêng của skill mình cần (VD result.get("prd"), result.get("spine")).
    KHÔNG raise exception.
    """
    text = (raw_output or "").strip()
    if not text:
        return {"status": "unknown"}

    # Thử tìm JSON hợp lệ ở vài dòng cuối cùng trước (giống parse_headless_result)
    tail_lines = text.splitlines()
    for line in reversed(tail_lines[-8:]):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                obj = json.loads(line)
                if isinstance(obj, dict) and "status" in obj:
                    return obj
            except json.JSONDecodeError:
                continue

    # Fallback: tìm khối {...} lớn nhất ở cuối văn bản (JSON có thể bị
    # xuống dòng nhiều chỗ, ví dụ có mảng open_questions nhiều phần tử).
    last_brace_open = text.rfind("{")
    if last_brace_open != -1:
        candidate = text[last_brace_open:]
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict) and "status" in obj:
                return obj
        except json.JSONDecodeError:
            pass

    return {"status": "unknown"}


def parse_headless_result(raw_output: str) -> BmadHeadlessResult:
    """Tìm dòng JSON cuối cùng khớp schema trong output của agent. Nếu
    không tìm thấy (agent không tuân thủ quy tắc) -> status "unknown",
    KHÔNG raise exception — caller tự quyết định coi "unknown" như thế nào
    (an toàn nhất: coi như "partial", không tự tin là "complete")."""
    matches = _JSON_TAIL_RE.findall(raw_output or "")
    if not matches:
        # thử tìm khối JSON lớn hơn ở cuối văn bản (fallback rộng hơn regex trên)
        tail = (raw_output or "").strip().splitlines()
        for line in reversed(tail[-5:]):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    obj = json.loads(line)
                    if "status" in obj:
                        return BmadHeadlessResult(
                            status=obj.get("status", "unknown"),
                            summary=obj.get("summary", ""),
                            assumptions=obj.get("assumptions", []),
                            open_questions=obj.get("open_questions", []),
                            raw_output=raw_output,
                        )
                except json.JSONDecodeError:
                    pass
        return BmadHeadlessResult(
            status="unknown", summary="", assumptions=[], open_questions=[],
            raw_output=raw_output,
        )

    # Lấy khối JSON khớp cuối cùng trong output (agent có thể nhắc tới JSON
    # ở giữa bài, ta chỉ tin dòng CUỐI theo đúng quy tắc đã yêu cầu).
    last_match_text = matches[-1]
    try:
        obj = json.loads(last_match_text)
    except json.JSONDecodeError:
        return BmadHeadlessResult(
            status="unknown", summary="", assumptions=[], open_questions=[],
            raw_output=raw_output,
        )

    return BmadHeadlessResult(
        status=obj.get("status", "unknown"),
        summary=obj.get("summary", ""),
        assumptions=obj.get("assumptions", []),
        open_questions=obj.get("open_questions", []),
        raw_output=raw_output,
    )
