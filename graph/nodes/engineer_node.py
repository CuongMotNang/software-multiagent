"""Engineer Node - Code generation using OpenHands Software Agent SDK.

This node receives design_doc + mockup_html from state and uses the
OpenHands SDK (openhands-sdk) to generate real code in a per-thread workspace.

FIXED (bản này): graph chạy BÊN TRONG container Docker Linux, không có WSL.
Bản cũ gọi `subprocess.run(["wsl", ...])` → FileNotFoundError ngay lập tức.
Giờ import openhands.sdk trực tiếp trong cùng process Python, bỏ toàn bộ
subprocess/WSL/path-conversion.

Timeout: dùng ThreadPoolExecutor + .result(timeout=900) để giữ cơ chế timeout
của bản cũ, tránh LLM treo block worker thread vô hạn.
"""

import os
import concurrent.futures
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv

# Load .env so this module works whether it's imported by graph_builder.py
# (which already calls load_dotenv elsewhere) or run standalone via
# `python -m graph.nodes.engineer_node`.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# Artifact Store imports
import sys
_graph_root = Path(__file__).resolve().parent.parent.parent
if str(_graph_root) not in sys.path:
    sys.path.insert(0, str(_graph_root))
from graph.repo_store import save_engineer_log, read_design, read_latest_mockup_screens

# Optional logging
try:
    from loguru import logger
    logger.enable("softwarefactory")
except ImportError:
    import logging
    logger = logging.getLogger("softwarefactory")
    logging.basicConfig(level=logging.INFO)


# === Constants ===

SANDBOX_BASE = Path(__file__).parent.parent.parent / "sandbox"
DEFAULT_MODEL = "anthropic/claude-sonnet-4-6"
DEFAULT_TIMEOUT = 900  # 15 minutes
MAX_LOG_CHARS = 5000


# === OpenHands SDK runner (in-process, có timeout) ===

def _run_openhands_sdk(
    workspace_path: Path,
    task_content: str,
    model: str,
    api_key: str,
    base_url: str,
) -> Dict[str, Any]:
    """Chạy OpenHands SDK trực tiếp trong process hiện tại (container Linux),
    thay cho việc gọi ra ngoài qua subprocess + WSL như bản cũ.

    Trả về dict: {"status": "completed"|"failed", "files": [...], "error": ...}
    """
    from openhands.sdk import LLM, Agent, Conversation, Tool
    from openhands.tools.file_editor import FileEditorTool
    from openhands.tools.terminal import TerminalTool
    from openhands.tools.task_tracker import TaskTrackerTool

    workspace_path.mkdir(parents=True, exist_ok=True)
    (workspace_path / "TASK.md").write_text(task_content, encoding="utf-8")

    # Snapshot files BEFORE the agent runs, để detect file mới tạo ra.
    before_files = {str(f) for f in workspace_path.rglob("*") if f.is_file()}

    _base_url = base_url or None  # empty string → None (vd: Anthropic direct)
    llm = LLM(
        model=model,
        api_key=api_key,
        base_url=_base_url,
        max_input_tokens=128000,
        max_output_tokens=8192,
    )

    # tools=[...] là BẮT BUỘC — không có thì agent không thể ghi file hay
    # chạy terminal command, chỉ sinh text mà thôi.
    agent = Agent(
        llm=llm,
        tools=[
            Tool(name=TerminalTool.name),
            Tool(name=FileEditorTool.name),
            Tool(name=TaskTrackerTool.name),
        ],
    )

    try:
        conversation = Conversation(agent=agent, workspace=str(workspace_path))
        conversation.send_message(task_content)
        conversation.run()

        after_files = {str(f) for f in workspace_path.rglob("*") if f.is_file()}
        new_files = sorted(
            f for f in (after_files - before_files) if not f.endswith("TASK.md")
        )
        return {"status": "completed", "files": new_files[:100]}
    except Exception as e:
        return {"status": "failed", "error": str(e)[:2000]}


def _run_with_timeout(
    workspace_path: Path,
    task_content: str,
    model: str,
    api_key: str,
    base_url: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """Wrap _run_openhands_sdk trong ThreadPoolExecutor để giữ cơ chế timeout
    (Python không có timeout built-in cho code đồng bộ trong cùng thread).
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            _run_openhands_sdk,
            workspace_path, task_content, model, api_key, base_url,
        )
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return {"status": "failed", "error": f"OpenHands SDK timed out after {timeout}s"}


# === Main Node Function ===

def engineer_node(state: Any, config: Dict[str, Any]) -> Dict[str, Any]:
    """Generate code using OpenHands SDK trực tiếp (in-process, container Linux).

    Args:
        state: SoftwareFactoryState (Pydantic BaseModel) -- accessed via
            dot-notation (state.design_doc).
        config: LangGraph configurable (must contain thread_id)

    Returns:
        State updates: repo_path, engineer_log, status
    """
    logger.info("Starting engineer_node (OpenHands SDK in-process)")

    design_doc = state.design_doc
    mockup_html = state.mockup_html
    thread_id = config.get("configurable", {}).get("thread_id", "default")

    if not design_doc:
        # Fallback: đọc từ Artifact Store
        design_doc = read_design(thread_id)
        if not design_doc:
            logger.warning("No design_doc, using default")
            design_doc = "Generate a simple hello world application."

    if not mockup_html:
        # Fix bug: ui_node() không set state.mockup_html nữa (chuyển sang lưu
        # nhiều màn hình qua repo_store) — nếu không fallback ở đây,
        # engineer_node LUÔN nhận mockup rỗng dù mockup đã được duyệt.
        # Từ Giai đoạn 3.3: mockup giờ là UI JSON (không phải HTML tự do) —
        # vẫn đọc được bình thường làm ngữ cảnh text cho LLM.
        screen_paths = read_latest_mockup_screens(thread_id)
        if screen_paths:
            parts = []
            for p in screen_paths:
                try:
                    parts.append(f"<!-- Screen: {p.stem} (UI JSON) -->\n{p.read_text(encoding='utf-8')}")
                except Exception as e:
                    logger.warning(f"Không đọc được mockup screen {p}: {e}")
            mockup_html = "\n\n".join(parts)
        if not mockup_html:
            logger.warning("No mockup_html (kể cả sau fallback từ repoStore)")

    workspace_path = SANDBOX_BASE / "workspace" / thread_id
    workspace_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Workspace: {workspace_path}")

    model = os.environ.get("LLM_MODEL", DEFAULT_MODEL)
    api_key = os.environ.get("OPENHANDS_LLM_API_KEY", "")
    base_url = os.environ.get("LLM_BASE_URL", "")

    if not api_key:
        logger.error("OPENHANDS_LLM_API_KEY not set")
        return {
            "repo_path": str(workspace_path),
            "engineer_log": "ERROR: OPENHANDS_LLM_API_KEY not configured.",
            "status": "failed",
        }

    # Build task content (giống hệt _build_sdk_script bản cũ, không đổi)
    task_content = (
        "# Code Generation Task\n\n"
        f"## Design Document\n\n{design_doc}\n\n"
        f"## Mockup HTML\n\n{mockup_html or '(No mockup)'}\n\n"
        "## Instructions\n"
        "Generate complete, runnable code based on the design above.\n"
        "- Create all necessary files in the workspace\n"
        "- Use best practices and proper project structure\n"
        "- Include dependencies (package.json, requirements.txt, etc.)\n"
        "- Document how to run the project\n"
    )

    logger.info("Running OpenHands SDK in-process...")
    data = _run_with_timeout(
        workspace_path, task_content, model, api_key, base_url, DEFAULT_TIMEOUT
    )

    # === Parse result ===
    # data đã là dict Python thật (không cần parse từ stdout text như bản cũ)
    if data.get("status") == "failed":
        eng_log = f"OpenHands error: {data.get('error', 'Unknown')}"
        st = "failed"
    else:
        files = data.get("files", [])
        eng_log = f"OpenHands completed OK.\nNew files: {len(files)}\n"
        if files:
            eng_log += "\n".join(f"  - {f}" for f in files[:30])
        else:
            eng_log += "(No new files were created -- check the task/model/log.)"
        st = "running"

    if len(eng_log) > MAX_LOG_CHARS:
        eng_log = eng_log[:MAX_LOG_CHARS] + "\n... (truncated)"

    # Lưu engineer log vào Artifact Store
    save_engineer_log(thread_id, eng_log)

    return {
        "repo_path": str(workspace_path),
        "engineer_log": eng_log,
        "status": st,
    }


# === LangGraph Node Export ===

from langchain_core.runnables import RunnableConfig


def ENGINEER_NODE(state: Any, config: RunnableConfig = None) -> Dict[str, Any]:
    return engineer_node(state, config or {"configurable": {}})


# === Entry Point (for manual testing) ===

if __name__ == "__main__":
    from graph.state import SoftwareFactoryState
    import json

    test_state = SoftwareFactoryState(
        design_doc="Create a simple Python web app with Flask",
        mockup_html="<html><body><h1>Hello</h1></body></html>",
    )
    test_config = {"configurable": {"thread_id": "test_engineer_001"}}
    result = engineer_node(test_state, test_config)
    print(json.dumps(result, indent=2, ensure_ascii=False))