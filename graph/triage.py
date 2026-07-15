"""Triage — phân loại finding + quyết định routing sau critic pass.

Nguồn: bmm-skills/4-implementation/bmad-dev-auto/step-04-review.md (đã
verify). 5 nhóm gốc của BMAD, tổng quát hoá cho artifact bất kỳ (không chỉ
code diff):

    patch      — sửa được tại chỗ, không cần quay lại node trước
    bad_spec   — nguyên nhân nằm ở INPUT từ node trước (chưa đủ rõ), nhưng
                 không phải mơ hồ tuyệt đối -> quay lại node trước sửa
    intent_gap — nguyên nhân nằm ngay trong yêu cầu GỐC đã chốt (qua gate
                 người rồi) -> không được đoán, phải HALT hỏi người
    defer      — có thật nhưng không do thay đổi hiện tại gây ra -> log
                 riêng, không chặn gate hiện tại
    reject     — nhiễu, bỏ qua

Quan trọng (đúng nguyên văn BMAD): "Disregard any severity assigned by a
reviewing subagent" — verdict/findings do critic.py trả về chỉ là NGUYÊN
LIỆU, quyết định severity + category cuối cùng do bước triage này (1 lệnh
gọi LLM riêng, đóng vai trò orchestrator) thực hiện, không tin trực tiếp
lens.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Literal

from graph.llm import llm_factory

Category = Literal["patch", "bad_spec", "intent_gap", "defer", "reject"]
Severity = Literal["low", "medium", "high"]

MAX_REVIEW_LOOP_ITERATIONS = int(os.getenv("MAX_REVIEW_LOOP_ITERATIONS", "5"))

_TRIAGE_SYSTEM_PROMPT = """Bạn là orchestrator triage trong 1 software factory nhiều agent.
Bạn nhận được findings từ nhiều critic lens ĐỘC LẬP (không biết nhau) về 1 artifact.
Nhiệm vụ: với MỖI finding, gán đúng 1 category và 1 severity, bỏ qua verdict/severity
lens tự gán (lens không đủ context để quyết severity cuối).

Category (chọn đúng 1):
- patch: sửa được ngay trong phạm vi artifact hiện tại, không cần input mới từ node trước
- bad_spec: nguyên nhân là do INPUT/tài liệu từ node TRƯỚC (upstream) chưa đủ rõ/thiếu sót,
  nhưng câu hỏi đặt ra có thể trả lời được nếu node trước bổ sung/sửa
- intent_gap: nguyên nhân nằm ngay trong yêu cầu GỐC đã được người duyệt chốt — bản thân
  yêu cầu đó mơ hồ/mâu thuẫn, KHÔNG được tự đoán, bắt buộc hỏi người
- defer: vấn đề có thật nhưng KHÔNG liên quan đến thay đổi đang xét, phát hiện tình cờ
- reject: không đủ căn cứ, nhiễu

Severity (low/medium/high): dựa trên hậu quả cho người dùng cuối/đối tượng tiêu thụ
artifact này, KHÔNG dựa trên cách lens diễn đạt.

Trả lời DUY NHẤT bằng JSON, không thêm chữ nào khác, đúng format:
{
  "findings": [
    {"lens": "<lens_id>", "description": "<tóm tắt 1 câu>", "category": "...", "severity": "..."}
  ]
}
Nếu không có finding thật sự nào (mọi lens đều ok), trả về {"findings": []}.
"""


def classify_findings(
    critic_summary: Dict[str, Dict[str, Any]],
    provider: str | None = None,
) -> List[Dict[str, str]]:
    """Gọi 1 lệnh LLM riêng (orchestrator) để phân loại toàn bộ findings.

    critic_summary: output của critic.run_critic_pass() — {lens_id: {...}}
    """
    raw_findings = []
    for lens_id, data in critic_summary.items():
        for f in data.get("findings", []):
            raw_findings.append({"lens": lens_id, "raw": f})

    if not raw_findings:
        return []

    llm = llm_factory(provider)
    user_prompt = "Findings cần phân loại:\n\n" + "\n".join(
        f"- [{f['lens']}] {f['raw']}" for f in raw_findings
    )
    resp = llm.call(
        system_prompt=_TRIAGE_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.0,
        max_tokens=2048,
    )
    if not resp.content:
        # Fail-safe: không đoán mò — coi như cần người xem, không âm thầm bỏ qua.
        return [
            {"lens": f["lens"], "description": f["raw"], "category": "intent_gap", "severity": "medium"}
            for f in raw_findings
        ]

    try:
        text = resp.content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            text = text.split("\n", 1)[1] if "\n" in text else text
        parsed = json.loads(text)
        return parsed.get("findings", [])
    except Exception:
        # Parse lỗi -> fail-safe giống trên, không silently drop.
        return [
            {"lens": f["lens"], "description": f["raw"], "category": "intent_gap", "severity": "medium"}
            for f in raw_findings
        ]


def decide_routing(
    findings: List[Dict[str, str]],
    loop_iteration: int,
    max_iterations: int = MAX_REVIEW_LOOP_ITERATIONS,
) -> Dict[str, Any]:
    """Quyết định hành động tiếp theo từ danh sách findings đã triage.

    Thứ tự ưu tiên (giống cascading order của dev-auto/step-04-review.md):
    intent_gap > bad_spec > patch > (chỉ defer/reject hoặc rỗng) -> proceed.

    Non-convergence guard: nếu bad_spec lặp quá max_iterations -> ép sang
    halt_escalate thay vì lặp lại vô hạn.
    """
    categories = {f.get("category") for f in findings}

    if "intent_gap" in categories:
        questions = [f["description"] for f in findings if f.get("category") == "intent_gap"]
        return {
            "action": "halt_escalate",
            "reason": "intent_gap",
            "questions": questions,
        }

    if "bad_spec" in categories:
        if loop_iteration >= max_iterations:
            questions = [f["description"] for f in findings if f.get("category") == "bad_spec"]
            return {
                "action": "halt_escalate",
                "reason": f"non-convergence sau {loop_iteration} vòng bad_spec-loopback",
                "questions": questions,
            }
        bad_spec_items = [f["description"] for f in findings if f.get("category") == "bad_spec"]
        return {
            "action": "loop_upstream",
            "reason": "bad_spec",
            "feedback": "\n".join(f"- {d}" for d in bad_spec_items),
        }

    if "patch" in categories:
        patch_items = [f["description"] for f in findings if f.get("category") == "patch"]
        return {
            "action": "auto_patch",
            "reason": "patch",
            "feedback": "\n".join(f"- {d}" for d in patch_items),
        }

    # Chỉ còn defer/reject hoặc rỗng -> không chặn, đi tiếp tới gate người.
    deferred = [f["description"] for f in findings if f.get("category") == "defer"]
    return {"action": "proceed", "reason": "defer_or_clean", "deferred": deferred}
