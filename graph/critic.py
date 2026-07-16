"""Critic pass — parallel review layers với context isolation.

Nguồn cảm hứng (đã verify trong repo BMAD-METHOD, không tự bịa thêm):
- bmm-skills/3-solutioning/bmad-architecture/references/reviewer-gate.md
  ("the parent never holds full review text")
- bmm-skills/4-implementation/bmad-code-review/customize.toml
  (roster cố định: Blind Hunter / Edge Case Hunter / Verification Gap
  Reviewer / Acceptance Auditor, mỗi lens là 1 subagent KHÔNG có context
  hội thoại trước)

Cách dùng:
    lenses = [
        CriticLens(id="feasibility", name="Feasibility",
                   system_prompt="..."),
        ...
    ]
    summary = run_critic_pass(thread_id, "prd", artifact_text=prd_v1,
                               lenses=lenses, context="...")
    # summary = {lens_id: {"verdict": "ok"|"concerns", "findings": [...],
    #                       "report_path": "critic/prd/feasibility.md"}}

QUAN TRỌNG: mỗi lens gọi LLM với system_prompt RIÊNG, KHÔNG kèm lịch sử hội
thoại của node cha — đúng tinh thần "no prior conversation context" của
BMAD. Nếu sau này đổi sang thật sự multi-agent (subagent runtime riêng),
chỉ cần thay _call_lens() bên dưới, phần còn lại không đổi.
"""
from __future__ import annotations

import concurrent.futures
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from graph.llm import llm_factory
from graph.repo_store import save_critic_report

try:
    from loguru import logger
    logger.enable("softwarefactory")
except ImportError:  # pragma: no cover
    import logging
    logger = logging.getLogger("softwarefactory")


@dataclass
class CriticLens:
    """1 góc nhìn phản biện độc lập (tương đương 1 'review layer' của BMAD)."""
    id: str
    name: str
    system_prompt: str
    # provider riêng cho lens này nếu muốn (None = dùng mặc định của process)
    provider: Optional[str] = None


# Format bắt buộc mọi lens phải tuân theo, để orchestrator parse được summary
# gọn mà không cần đọc lại full report. Không dùng điểm số/severity ở bước
# này (đúng tinh thần checkpoint-preview.md: máy chỉ tag, người/triage-step
# sau mới phán mức nghiêm trọng).
_LENS_OUTPUT_CONTRACT = """
Trả lời theo ĐÚNG format sau, không thêm gì khác ở đầu:

VERDICT: ok | concerns

FINDINGS:
- <mỗi finding 1 dòng, ngắn gọn, nêu rõ bằng chứng cụ thể>
- (để trống nếu VERDICT: ok)

Sau đó có thể viết phần giải thích/chi tiết dài hơn bên dưới — phần đó sẽ
được lưu đầy đủ ra file, không hiện cho vòng triage tiếp theo.
"""


def _call_lens(lens: CriticLens, artifact_text: str, context: str) -> str:
    """Gọi 1 lens — KHÔNG truyền lịch sử hội thoại của node cha vào đây."""
    llm = llm_factory(lens.provider)
    system_prompt = lens.system_prompt.rstrip() + "\n\n" + _LENS_OUTPUT_CONTRACT
    user_prompt = (
        f"## NGỮ CẢNH\n{context}\n\n## NỘI DUNG CẦN REVIEW\n\n{artifact_text}"
        if context else
        f"## NỘI DUNG CẦN REVIEW\n\n{artifact_text}"
    )
    resp = llm.call(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.2, max_tokens=4096)
    return resp.content or "VERDICT: concerns\nFINDINGS:\n- LLM không trả về kết quả (lỗi gọi model)."


def _parse_lens_output(raw: str) -> Dict[str, Any]:
    verdict_match = re.search(r"VERDICT:\s*(ok|concerns)", raw, re.IGNORECASE)
    verdict = verdict_match.group(1).lower() if verdict_match else "concerns"

    findings: List[str] = []
    findings_block_match = re.search(
        r"FINDINGS:\s*(.*?)(?:\n\n|\Z)", raw, re.IGNORECASE | re.DOTALL
    )
    if findings_block_match:
        for line in findings_block_match.group(1).splitlines():
            line = line.strip().lstrip("-").strip()
            if line:
                findings.append(line)

    return {"verdict": verdict, "findings": findings}


def run_critic_pass(
    thread_id: str,
    node_name: str,
    artifact_text: str,
    lenses: List[CriticLens],
    context: str = "",
) -> Dict[str, Dict[str, Any]]:
    """Chạy N lens SONG SONG, mỗi lens context-isolated.

    Trả về summary gọn theo từng lens — parent KHÔNG giữ full report, chỉ
    giữ verdict + findings ngắn + đường dẫn file (đúng pattern context
    isolation của reviewer-gate.md).
    """
    summary: Dict[str, Dict[str, Any]] = {}

    if not lenses:
        return summary

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(lenses)) as executor:
        future_to_lens = {
            executor.submit(_call_lens, lens, artifact_text, context): lens
            for lens in lenses
        }
        # Bước 1: chỉ THU THẬP raw output — KHÔNG commit ở đây. as_completed
        # chạy trong main thread nên các lệnh git vốn đã tuần tự với nhau,
        # nhưng tách hẳn 2 bước ra cho rõ ràng + để lỗi commit của 1 lens
        # không làm mất raw output của các lens khác đã chạy xong.
        collected: List[tuple[CriticLens, str]] = []
        for future in concurrent.futures.as_completed(future_to_lens):
            lens = future_to_lens[future]
            try:
                raw = future.result()
            except Exception as e:  # pragma: no cover
                logger.exception(f"Critic lens '{lens.id}' failed")
                raw = f"VERDICT: concerns\nFINDINGS:\n- Lỗi khi chạy lens: {e}"
            collected.append((lens, raw))

    # Bước 2: commit TUẦN TỰ trong main thread. Nếu 1 lens lỗi commit (VD
    # git lock), các lens khác vẫn được lưu — không để 1 lỗi hạ tầng làm mất
    # toàn bộ kết quả critic pass đã tốn tiền gọi LLM.
    for lens, raw in collected:
        parsed = _parse_lens_output(raw)
        try:
            report_path = save_critic_report(thread_id, node_name, lens.id, raw)
        except Exception as e:
            logger.exception(f"Không commit được critic report cho lens '{lens.id}'")
            report_path = ""
            parsed["findings"] = parsed["findings"] + [
                f"(CẢNH BÁO: report của lens này lưu thất bại — {e})"
            ]

        summary[lens.id] = {
            "name": lens.name,
            "verdict": parsed["verdict"],
            "findings": parsed["findings"],
            "report_path": report_path,
        }

    return summary
