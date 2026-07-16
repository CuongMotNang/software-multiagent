"""Node Tech Writer — Paige: tổng hợp PRD + UX Spec + Design Document + log
engineer thành 1 README handoff DUY NHẤT, chạy cuối pipeline (sau engineer,
trước END). Không có gate, không phải input cho node nào khác — đây là
tài liệu bàn giao cho người đọc sau, không phải artifact trung gian.
"""
import os
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig

from graph.state import (
    SoftwareFactoryState,
    update_node_stats,
    push_content_history,
)
from graph.llm import llm_factory
from graph.repo_store import (
    save_tech_docs, read_prd, read_ux_spec, read_design, read_engineer_log,
)
from graph.prompt_loader import load_prompt

# Log engineer có thể rất dài (JSONL truncated) — giữ vừa đủ ngữ cảnh, không
# đẩy nguyên văn hàng chục nghìn ký tự vào prompt của Paige.
MAX_ENGINEER_LOG_CHARS = 4000


def tech_writer_node(state: SoftwareFactoryState, config: RunnableConfig | None = None) -> Dict[str, Any]:
    """Node Tech Writer: prd + ux_spec + design_doc + engineer_log -> tech_docs (README)."""
    thread_id = "default"
    if config:
        configurable = config.get("configurable", {}) or {}
        thread_id = configurable.get("thread_id", "default")

    prd = state.prd_approved.strip() or state.prd_v1.strip() or read_prd(thread_id)
    ux_spec = state.ux_spec.strip() or read_ux_spec(thread_id)
    design_doc = state.design_doc.strip() or read_design(thread_id)
    engineer_log = state.engineer_log.strip() or read_engineer_log(thread_id)
    if len(engineer_log) > MAX_ENGINEER_LOG_CHARS:
        engineer_log = engineer_log[:MAX_ENGINEER_LOG_CHARS] + "\n... (truncated)"

    if not prd and not design_doc:
        # Không chặn pipeline vì thiếu tài liệu — Paige chỉ là bước tổng hợp
        # cuối, không nên halt cả 1 lượt chạy đã ra code chỉ vì thiếu docs.
        return {
            "tech_docs": "## LỖI: Không đủ tài liệu (PRD/Design) để viết README handoff.",
            "status": "running",
            "error": "prd and design_doc both empty khi vào tech_writer_node",
        }

    provider_name = os.getenv("TECHWRITER_PROVIDER", None)
    llm = llm_factory(provider_name)

    system_prompt = load_prompt("techwriter_system")
    user_prompt = (
        f"## PRD ĐÃ DUYỆT\n\n{prd or '(không có)'}\n\n"
        f"## UX SPEC\n\n{ux_spec or '(không có)'}\n\n"
        f"## DESIGN DOCUMENT\n\n{design_doc or '(không có)'}\n\n"
        f"## LOG ENGINEER (đã cắt bớt nếu quá dài)\n\n{engineer_log or '(không có)'}\n\n"
        "Hãy viết README.md handoff theo đúng cấu trúc đã quy định."
    )

    llm_response = llm.call(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=8000,
    )
    result = llm_response.content

    if result is None:
        return {
            "tech_docs": "## LỖI: LLM không trả về README.",
            "status": "running",
            "error": "LLM returned None",
        }

    save_tech_docs(thread_id, result)

    node_stats = update_node_stats(
        state.node_stats, "tech_writer",
        reject_count=0,
        tokens_used=llm_response.total_tokens,
        model=llm_response.model,
    )
    content_history = push_content_history(state.content_history, "tech_writer", result)

    return {
        "tech_docs": result,
        "status": "completed",
        "node_stats": node_stats,
        "content_history": content_history,
    }


# Alias để GraphBuilder dùng
TECH_WRITER_NODE = tech_writer_node
