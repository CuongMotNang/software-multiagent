"""Node Design Tokens — sinh design_tokens.json từ Design Document.

Chạy ngay sau khi gate_design approve, trước khi vào "ui" — để design_tokens
luôn sẵn sàng làm ngữ cảnh bắt buộc cho ui_node (Giai đoạn 3.2).
"""

import json
import os
from typing import Any, Dict

from langchain_core.runnables import RunnableConfig
from pydantic import ValidationError

from graph.state import (
    SoftwareFactoryState,
    update_node_stats,
    push_content_history,
)
from graph.llm import llm_factory
from graph.repo_store import save_design_tokens, read_design
from graph.prompt_loader import load_prompt
from graph.json_utils import strip_code_fence
from graph.schemas import DesignTokens


def _parse_and_validate(raw: str) -> tuple[DesignTokens | None, str | None]:
    """Trả về (tokens, None) nếu hợp lệ, hoặc (None, error_message) nếu không."""
    cleaned = strip_code_fence(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return None, f"JSON không hợp lệ: {e}"
    try:
        tokens = DesignTokens.model_validate(data)
    except ValidationError as e:
        return None, f"Sai schema: {e}"
    return tokens, None


def design_tokens_node(state: SoftwareFactoryState, config: RunnableConfig | None = None) -> Dict[str, Any]:
    """design_doc -> design_tokens (JSON string).

    Có retry 1 lần nếu LLM trả JSON sai schema/không parse được — kèm
    thông báo lỗi cụ thể vào lần gọi lại, giống tinh thần fallback ở
    ui_node._list_screens(), tránh trust thẳng output LLM.
    """
    thread_id = "default"
    if config:
        configurable = config.get("configurable", {}) or {}
        thread_id = configurable.get("thread_id", "default")

    design_doc = state.design_doc.strip()
    if not design_doc:
        design_doc = read_design(thread_id)

    if not design_doc:
        return {
            "design_tokens": "",
            "status": "failed",
            "error": "design_doc rỗng — không thể sinh design tokens",
        }

    provider_name = os.getenv("DESIGN_PROVIDER", None)
    llm = llm_factory(provider_name)
    system_prompt = load_prompt("design_tokens_system")
    user_prompt = f"## DESIGN DOCUMENT\n\n{design_doc}\n\nSinh design tokens JSON theo đúng quy tắc đã nêu."

    total_tokens = 0
    model_used = ""
    tokens: DesignTokens | None = None
    last_error = ""

    for attempt in range(2):  # thử tối đa 2 lần: 1 lần đầu + 1 lần retry kèm lỗi
        llm_response = llm.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt if attempt == 0 else (
                user_prompt
                + f"\n\nLẦN TRƯỚC BẠN TRẢ VỀ JSON SAI, LỖI CỤ THỂ:\n{last_error}\n"
                "Hãy sửa lại và CHỈ trả về đúng 1 khối JSON hợp lệ, không kèm gì khác."
            ),
            temperature=0.2,
            max_tokens=2000,
        )
        total_tokens += llm_response.total_tokens
        model_used = llm_response.model or model_used

        if llm_response.content is None:
            last_error = "LLM không trả về nội dung (network/API error)"
            continue

        tokens, err = _parse_and_validate(llm_response.content)
        if tokens is not None:
            break
        last_error = err or "Lỗi không xác định"

    if tokens is None:
        return {
            "design_tokens": "",
            "status": "failed",
            "error": f"Sinh design_tokens thất bại sau 2 lần thử: {last_error}",
        }

    tokens_json = json.dumps(tokens.model_dump(), indent=2, ensure_ascii=False)
    save_design_tokens(thread_id, tokens_json)

    node_stats = update_node_stats(
        state.node_stats, "design_tokens",
        reject_count=0,
        tokens_used=total_tokens,
        model=model_used,
    )
    content_history = push_content_history(state.content_history, "design_tokens", tokens_json)

    return {
        "design_tokens": tokens_json,
        "status": "running",
        "node_stats": node_stats,
        "content_history": content_history,
    }


# Alias để GraphBuilder dùng
DESIGN_TOKENS_NODE = design_tokens_node
