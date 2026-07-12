"""Agent Runtime — tầng trung gian giữa graph (LangGraph node) và SDK agent thật.

Kiến trúc 3 tầng đã thống nhất:
    TẦNG GRAPH (ba_node.py...) -> TẦNG AGENT RUNTIME (file này) -> TẦNG SDK (OpenHands)

Node chỉ gọi run_agent(runtime_name, task, cfg), không biết gì về OpenHands SDK bên
trong — đổi runtime (vd sang Claude Code sau này) chỉ cần thêm 1 hàm run_xxx() mới và
đăng ký vào RUNTIMES, không sửa node.

API của openhands-sdk dùng trong file này đã được verify bằng cách dựng object thật
(không suy đoán từ tài liệu) với openhands-sdk==1.35.0:
- `Conversation(agent=..., workspace=..., max_iteration_per_run=...)` — verify qua
  inspect.signature(Conversation.__init__) trực tiếp.
- Token usage lấy qua `conversation.conversation_stats.get_combined_metrics()
  .accumulated_token_usage.{prompt_tokens,completion_tokens}` — verify qua đọc
  source code thật của class Metrics.
- `stuck_detection=True` là mặc định sẵn có của SDK (không cần tự viết cơ chế chống
  lặp vô hạn như lo ngại ban đầu trong tài liệu kiến trúc).
- KHÔNG cấu hình SecurityAnalyzer/ConfirmationPolicy => mặc định KHÔNG treo chờ duyệt
  (đã verify: Conversation() không tự gắn policy nào nếu không truyền vào).

CHƯA verify (cần làm khi có API key thật, xem ghi chú trong run_openhands_text_agent):
- Hành vi thật của agent loop (chất lượng, số bước, tốc độ) với model NVIDIA NIM cụ thể.
- Rủi ro crash "security_risk nhưng không có analyzer" (GitHub issue #11309, bản
  1.35.0 — chưa rõ đã fix hay chưa, cần thử thật).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Literal, TypedDict

logger = logging.getLogger(__name__)


class AgentTask(TypedDict, total=False):
    instructions: str
    workspace_path: Path
    output_file: str  # tên file agent phải tạo ra trong workspace_path, vd "PRD.md"


class AgentResult(TypedDict):
    status: Literal["completed", "failed"]
    output: str
    log: str
    prompt_tokens: int
    completion_tokens: int
    model: str


def run_openhands_text_agent(task: AgentTask, cfg: dict[str, Any]) -> AgentResult:
    """Chạy 1 Agent OpenHands SDK dạng "text" — FileEditorTool + TaskTrackerTool,
    KHÔNG có Terminal/Browser. Dùng chung cho ba_node/prd_node/design_node.

    cfg cần có: model, api_key, base_url (optional), agent_context (optional,
    dùng cho Skill riêng từng node), max_iteration_per_run (optional, mặc định
    SDK là 500 — với text-only task nên set thấp hơn nhiều, vd 30, để tránh tốn
    token nếu agent bị lỗi logic).
    """
    from pydantic import SecretStr

    from openhands.sdk import LLM, Agent, Conversation, Tool
    from openhands.tools.file_editor import FileEditorTool
    from openhands.tools.task_tracker import TaskTrackerTool

    workspace_path: Path = task["workspace_path"]
    workspace_path.mkdir(parents=True, exist_ok=True)
    output_file = task.get("output_file", "OUTPUT.md")
    model = cfg["model"]

    llm = LLM(
        usage_id=cfg.get("usage_id", "text-agent"),
        model=model,
        api_key=SecretStr(cfg["api_key"]),
        base_url=cfg.get("base_url"),
    )
    agent = Agent(
        llm=llm,
        tools=[Tool(name=FileEditorTool.name), Tool(name=TaskTrackerTool.name)],
        agent_context=cfg.get("agent_context"),
    )

    conversation = Conversation(
        agent=agent,
        workspace=str(workspace_path),
        max_iteration_per_run=cfg.get("max_iteration_per_run", 30),
    )
    conversation.send_message(task["instructions"])

    try:
        conversation.run()
    except Exception as e:
        logger.exception("[agent_runtime] conversation.run() thất bại")
        return {
            "status": "failed",
            "output": "",
            "log": f"{type(e).__name__}: {e}"[:4000],
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "model": model,
        }

    metrics = conversation.conversation_stats.get_combined_metrics()
    usage = metrics.accumulated_token_usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0

    output_path = workspace_path / output_file
    if not output_path.exists():
        return {
            "status": "failed",
            "output": "",
            "log": f"Agent chạy xong nhưng không tạo ra file {output_file}",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "model": model,
        }

    return {
        "status": "completed",
        "output": output_path.read_text(encoding="utf-8"),
        "log": "ok",
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "model": model,
    }


RUNTIMES: dict[str, Callable[[AgentTask, dict[str, Any]], AgentResult]] = {
    "openhands_text": run_openhands_text_agent,
}


def run_agent(runtime_name: str, task: AgentTask, cfg: dict[str, Any]) -> AgentResult:
    if runtime_name not in RUNTIMES:
        raise ValueError(
            f"Unknown agent runtime: {runtime_name!r}. Có sẵn: {list(RUNTIMES)}"
        )
    return RUNTIMES[runtime_name](task, cfg)
