"""Debate room — agent-team debate point-to-point, có lead relay.

Nguồn (đã verify): core-skills/bmad-party-mode/references/mode-agent-team.md
— persona đứng (standing team), địa chỉ trực tiếp lẫn nhau (point-to-point),
KHÔNG có shared feed mặc định, 1 "lead" chịu trách nhiệm relay ngữ cảnh cho
ai bị "lỡ" một trao đổi trong lúc mình chưa tới lượt.

Khác với critic.py (mỗi lens chạy 1 lần, độc lập, không biết critic khác):
debate.py chạy NHIỀU VÒNG, các persona THẤY VÀ PHẢN HỒI LẪN NHAU — đây mới
là "họp" thật, critic pass không phải họp.

Cách dùng:
    personas = [
        DebatePersona(id="architect", name="Architect-lite", system_prompt="..."),
        DebatePersona(id="risk", name="Risk/BA-liaison", system_prompt="..."),
        DebatePersona(id="pm", name="PM", system_prompt="...", is_lead=True),
    ]
    synthesis = run_debate(thread_id, "prd", topic="...", personas=personas)
    # synthesis: str — bản kết luận do lead viết, dùng làm input cho producer node.
    # Transcript đầy đủ được lưu ra file qua repo_store, KHÔNG giữ trong state.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

from graph.llm import llm_factory
from graph.repo_store import save_debate_transcript

try:
    from loguru import logger
    logger.enable("softwarefactory")
except ImportError:  # pragma: no cover
    import logging
    logger = logging.getLogger("softwarefactory")

# Số vòng debate tối đa trước khi bắt buộc dừng + tổng hợp — cấu hình qua
# .env, KHÔNG tự detect hội thoại đã "hội tụ" hay chưa (giữ đơn giản).
N_DEBATE = int(os.getenv("N_DEBATE", "3"))


@dataclass
class DebatePersona:
    id: str
    name: str
    system_prompt: str
    is_lead: bool = False
    provider: Optional[str] = None


@dataclass
class _Message:
    round: int
    speaker_id: str
    speaker_name: str
    to: str  # id của 1 persona cụ thể, hoặc "all"
    content: str


def _resolve_target(raw_to: str, personas: List[DebatePersona]) -> str:
    """Khớp chuỗi 'TO: ...' agent tự viết (có thể ghi tên, không phải id)
    với đúng persona.id đã biết. Không khớp được -> coi như 'all'."""
    raw = raw_to.strip().lower()
    if raw in ("all", "everyone", "mọi người", "tất cả"):
        return "all"
    for p in personas:
        if raw == p.id.lower() or raw == p.name.lower() or raw in p.name.lower():
            return p.id
    return "all"


def _build_user_prompt(
    unseen: List[_Message], topic: str, round_no: int, total_rounds: int
) -> str:
    if unseen:
        history_block = "\n\n".join(
            f"[Vòng {m.round}] {m.speaker_name} nói (gửi tới: {m.to}):\n{m.content}"
            for m in unseen
        )
    else:
        history_block = "(Chưa có ai nói gì bạn cần phản hồi trước lượt này.)"

    return (
        f"## CHỦ ĐỀ THẢO LUẬN\n{topic}\n\n"
        f"## NHỮNG GÌ BẠN CẦN BIẾT TRƯỚC KHI PHÁT BIỂU (vòng {round_no}/{total_rounds})\n"
        f"{history_block}\n\n"
        "## YÊU CẦU\n"
        "Phát biểu lượt của bạn — ngắn gọn (3-6 câu), đi thẳng vào điểm bất "
        "đồng hoặc bổ sung thực chất, KHÔNG lặp lại điều người khác đã nói. "
        "Dòng ĐẦU TIÊN của câu trả lời bắt buộc ghi 'TO: <tên người bạn muốn "
        "nhắm tới>' hoặc 'TO: all' nếu nói chung cho cả phòng."
    )


def _call_persona(
    persona: DebatePersona, unseen: List[_Message], topic: str, round_no: int, total_rounds: int
) -> _Message:
    llm = llm_factory(persona.provider)
    user_prompt = _build_user_prompt(unseen, topic, round_no, total_rounds)
    resp = llm.call(
        system_prompt=persona.system_prompt,
        user_prompt=user_prompt,
        temperature=0.4,
        max_tokens=1024,
    )
    content = resp.content or "(không có phản hồi — lỗi gọi model)"

    to = "all"
    lines = content.splitlines()
    if lines and lines[0].strip().upper().startswith("TO:"):
        to = lines[0].split(":", 1)[1].strip()
        content = "\n".join(lines[1:]).strip()

    return _Message(
        round=round_no,
        speaker_id=persona.id,
        speaker_name=persona.name,
        to=to,
        content=content,
    )


def run_debate(
    thread_id: str,
    node_name: str,
    topic: str,
    personas: List[DebatePersona],
    n_rounds: Optional[int] = None,
) -> str:
    """Chạy debate point-to-point qua nhiều vòng, trả về bản synthesis cuối.

    Point-to-point + lead relay:
    - Mỗi persona thường CHỈ thấy message gửi tới mình ('to' == persona.id)
      hoặc gửi chung ('to' == "all"), tính TỪ SAU lần mình nói gần nhất.
    - Lead (is_lead=True) thấy TOÀN BỘ message từ sau lần lead nói gần nhất,
      không bị lọc theo 'to' — đây chính là cơ chế relay: nếu ai đó bị nhắc
      tên trong lúc chưa tới lượt, lead vẫn nắm được toàn cảnh để tổng hợp
      đúng ở bước cuối, kể cả khi 1 persona nào đó "bỏ lỡ" 1 nhịp.
    """
    if n_rounds is None:
        n_rounds = N_DEBATE

    lead = next((p for p in personas if p.is_lead), personas[-1])
    transcript: List[_Message] = []
    last_seen_index: Dict[str, int] = {p.id: 0 for p in personas}

    for round_no in range(1, n_rounds + 1):
        for persona in personas:
            window = transcript[last_seen_index[persona.id]:]
            if persona.is_lead:
                unseen = window  # lead thấy hết, không lọc theo 'to'
            else:
                unseen = [m for m in window if m.to == persona.id or m.to == "all"]

            msg = _call_persona(persona, unseen, topic, round_no, n_rounds)
            msg.to = _resolve_target(msg.to, personas)
            transcript.append(msg)
            last_seen_index[persona.id] = len(transcript)

    transcript_md = "\n\n---\n\n".join(
        f"**[Vòng {m.round}] {m.speaker_name} -> {m.to}**\n\n{m.content}"
        for m in transcript
    )
    save_debate_transcript(thread_id, node_name, transcript_md)

    synthesis_prompt = (
        f"Bạn (lead) vừa điều phối 1 buổi thảo luận {n_rounds} vòng về chủ đề:\n{topic}\n\n"
        f"Toàn bộ nội dung thảo luận:\n\n{transcript_md}\n\n"
        "Hãy tổng hợp thành 1 bản kết luận ngắn gọn cho người viết tài liệu "
        "tiếp theo áp dụng ngay: (1) các điểm đã thống nhất, (2) các điểm còn "
        "bất đồng nếu có (nêu rõ, không tự ý chọn 1 phe), (3) khuyến nghị cụ "
        "thể. Viết lại bằng lời của bạn, không chép nguyên văn từng câu."
    )
    llm = llm_factory(lead.provider)
    resp = llm.call(
        system_prompt=lead.system_prompt,
        user_prompt=synthesis_prompt,
        temperature=0.3,
        max_tokens=2048,
    )
    return resp.content or "(Lead không tổng hợp được — xem transcript đầy đủ trong repo_store.)"
