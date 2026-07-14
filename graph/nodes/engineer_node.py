"""Engineer Node - Code generation using OpenCode agent (opencode serve HTTP REST).

Hỗ trợ 2 runtime:
1. OpenCode agent (mới, bật qua ENGINEER_USE_AGENT=true)
2. OpenHands SDK (cũ, mặc định để không phá vỡ hành vi hiện tại)
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
from graph.repo_store import AGENT_WORKSPACE_ROOT
DEFAULT_MODEL = "anthropic/claude-sonnet-4-6"
DEFAULT_TIMEOUT = 900  # 15 minutes
MAX_LOG_CHARS = 5000


# === OpenHands SDK runner (in-process, có timeout) — giữ cho nhánh cũ ===

def _run_openhands_sdk(
    workspace_path: Path,
    task_content: str,
    model: str,
    api_key: str,
    base_url: str,
) -> Dict[str, Any]:
    """Chạy OpenHands SDK trực tiếp trong process hiện tại (container Linux),

    Có timeout: dùng ThreadPoolExecutor gọi blocking SDK call + .result(timeout=...)
    tránh treo worker thread vô hạn.

    Returns dict với keys:
    - status: "completed" | "failed"
    - files: list[str] (file names đã tạo/sửa)
    - error: str (nếu có lỗi)
    """
    def _call_sdk():
        try:
            from openhands.sdk import OpenHands
            sdk = OpenHands(
                model=model or DEFAULT_MODEL,
                api_key=api_key,
                base_url=base_url,
                workspace=str(workspace_path),
            )
            result = sdk.run(task_content)
            # SDK result format: trả về dict với event list
            created_files = []
            if result and hasattr(result, "events"):
                for ev in result.events:
                    if hasattr(ev, "path") and ev.path:
                        created_files.append(str(ev.path))
            return {"status": "completed", "files": created_files}
        except Exception as e:
            logger.exception("OpenHands SDK call failed")
            return {"status": "failed", "error": str(e)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_call_sdk)
        try:
            return future.result(timeout=DEFAULT_TIMEOUT)
        except concurrent.futures.TimeoutError:
            logger.warning(f"OpenHands SDK timed out after {DEFAULT_TIMEOUT}s")
            return {"status": "failed", "error": f"Timeout after {DEFAULT_TIMEOUT}s"}
        except Exception as e:
            logger.exception("Unexpected error in _run_openhands_sdk")
            return {"status": "failed", "error": str(e)}


# === OpenCode agent runner (mới) ===

def _engineer_node_agentic(state: Any, thread_id: str, design_doc: str, mockup_html: str) -> Dict[str, Any]:
    """Dùng OpenCode agent (opencode serve HTTP REST) — generate code trong projects_data workspace."""
    from graph.agent_runtime import run_agent

    # Workspace trong AGENT_WORKSPACE_ROOT/<threadID>/engineer_work
    workspace_path = AGENT_WORKSPACE_ROOT / thread_id / "engineer_work"

    # Build task content cho agent
    mockup_block = mockup_html or "(No mockup)"
    instructions = f"""# Code Generation Task

## Design Document
{design_doc}

## Mockup HTML
{mockup_block}

## Instructions
Generate complete, runnable code based on the design and mockup above.
- Create all necessary files in the workspace directory
- Use best practices and proper project structure
- Include dependencies (package.json, requirements.txt, etc.)
- Document how to run the project (README.md)
- Code phải thực sự chạy được (npm run dev / python app.py / etc.)
"""

    cfg = {
        "model": os.getenv("ENGINEER_LLM_MODEL", os.getenv("LLM_MODEL", DEFAULT_MODEL)),
        "api_key": os.getenv("ENGINEER_LLM_API_KEY", os.getenv("OPENHANDS_LLM_API_KEY", "")),
        "base_url": os.getenv("ENGINEER_LLM_BASE_URL", os.getenv("LLM_BASE_URL", "")),
    }

    result = run_agent(
        "opencode",
        {"instructions": instructions, "workspace_path": workspace_path, "output_file": None},
        cfg,
    )

    if result["status"] != "completed":
        eng_log = f"OpenCode error: {result['log']}"
        return {
            "repo_path": str(workspace_path),
            "engineer_log": eng_log,
            "status": "failed",
        }

    # List generated files
    files = []
    if workspace_path.exists():
        for f in workspace_path.rglob("*"):
            if f.is_file():
                files.append(str(f.relative_to(workspace_path)))

    eng_log = f"OpenCode completed OK.\nNew files: {len(files)}\n"
    if files:
        eng_log += "\n".join(f"  - {f}" for f in files[:30])
    else:
        eng_log += "(No new files were created -- check the task/model/log.)"

    if len(eng_log) > MAX_LOG_CHARS:
        eng_log = eng_log[:MAX_LOG_CHARS] + "\n... (truncated)"

    save_engineer_log(thread_id, eng_log)

    return {
        "repo_path": str(workspace_path),
        "engineer_log": eng_log,
        "status": "running",
    }


def _engineer_node_simple(state: Any, thread_id: str, design_doc: str, mockup_html: str) -> Dict[str, Any]:
    """Cách cũ: OpenHands SDK, workspace sandbox/workspace/<threadID>."""
    workspace_path = SANDBOX_BASE / "workspace" / thread_id
    workspace_path.mkdir(parents=True, exist_ok=True)

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

    mockup_block = mockup_html or "(No mockup)"
    task_content = (
        "# Code Generation Task\n\n"
        f"## Design Document\n\n{design_doc}\n\n"
        f"## Mockup HTML\n\n{mockup_block}\n\n"
        "## Instructions\n"
        "Generate complete, runnable code based on the design above.\n"
        "- Create all necessary files in the workspace\n"
        "- Use best practices and proper project structure\n"
        "- Include dependencies (package.json, requirements.txt, etc.)\n"
        "- Document how to run the project\n"
    )

    logger.info("Running OpenHands SDK in-process...")
    data = _run_openhands_sdk(
        workspace_path, task_content, model, api_key, base_url
    )

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

    save_engineer_log(thread_id, eng_log)

    return {
        "repo_path": str(workspace_path),
        "engineer_log": eng_log,
        "status": st,
    }


# === Main Node Function ===

def engineer_node(state: Any, config: Dict[str, Any]) -> Dict[str, Any]:
    """Generate code based on design_doc + mockup_html.

    Bật/tắt nhánh agentic (OpenCode) qua biến môi trường ENGINEER_USE_AGENT=true —
    mặc định TẮT (dùng OpenHands SDK cũ) để không phá vỡ hành vi hiện tại.

    Args:
        state: SoftwareFactoryState (Pydantic BaseModel)
        config: LangGraph configurable (must contain thread_id)

    Returns:
        State updates: repo_path, engineer_log, status
    """
    logger.info("Starting engineer_node")

    design_doc = state.design_doc
    mockup_html = state.mockup_html
    thread_id = config.get("configurable", {}).get("thread_id", "default")

    if not design_doc:
        design_doc = read_design(thread_id)
        if not design_doc:
            logger.warning("No design_doc, using default")
            design_doc = "Generate a simple hello world application."

    if not mockup_html:
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

    use_agent = os.getenv("ENGINEER_USE_AGENT", "false").strip().lower() in ("1", "true", "yes")
    if use_agent:
        return _engineer_node_agentic(state, thread_id, design_doc, mockup_html)
    return _engineer_node_simple(state, thread_id, design_doc, mockup_html)


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