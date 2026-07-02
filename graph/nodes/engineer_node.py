"""Engineer Node - Code generation using OpenHands Software Agent SDK.

This node receives design_doc + mockup_html from state and uses the
OpenHands SDK (openhands-sdk, real package -- see docs.openhands.dev/sdk)
via a WSL Python venv to generate real code in a per-thread workspace.

FIXED in this version (see review history for details):
- Agent now explicitly receives tools=[TerminalTool, FileEditorTool,
  TaskTrackerTool]. Without this the agent has ZERO capability to write
  files or run commands -- this was the critical bug in the first draft.
- LLM(...) now takes direct keyword args (model=, api_key=, base_url=, ...),
  not a data={...} dict.
- Uses the documented Conversation(agent=, workspace=<path str>) factory
  instead of manually constructing LocalConversation/LocalWorkspace with
  unverified extra kwargs.
- Success signal is a before/after file-set diff (pure stdlib), not an
  unverified event callback mechanism.
- state.design_doc / state.mockup_html use dot-notation because
  SoftwareFactoryState is a Pydantic BaseModel (confirmed from state.py),
  not a TypedDict/dict -- using .get() here raises AttributeError.
- ENGINEER_NODE's config param is typed as RunnableConfig with a default of
  None, and engineer_node() falls back to {"configurable": {}} if missing --
  works around LangGraph's config-injection relying on the parameter being
  annotated as RunnableConfig specifically.
- Reads OPENHANDS_LLM_API_KEY (not LLM_API_KEY) and LLM_BASE_URL from env,
  matching this project's actual .env convention -- the SDK script itself
  doesn't dictate any env var name since values are injected as literals
  into the generated script, so there's no real requirement to match the
  SDK's own example naming here. Keeping a distinct OPENHANDS_-prefixed key
  also avoids colliding with whatever generic LLM_MODEL/key the other nodes
  (ba/prd/design/ui) might already use for their own LLM calls.
- Auto-loads .env on import so this also works when run standalone via
  `python -m graph.nodes.engineer_node`, not only when graph_builder.py has
  already loaded it first.

KNOWN LIMITATION (not fixed here, flagged for a future decision):
LocalWorkspace executes directly in the WSL process -- there is NO Docker
sandbox in this path. working_dir is a convention, not a hard jail.
DockerWorkspace exists in the SDK for real container isolation, but its
exact mount/scoping parameters were not independently verified here.
"""

import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv

# Load .env so this module works whether it's imported by graph_builder.py
# (which already calls load_dotenv elsewhere) or run standalone via
# `python -m graph.nodes.engineer_node`.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# Artifact Store imports (import trực tiếp từ graph/artifact_store.py)
import sys
_graph_root = Path(__file__).resolve().parent.parent.parent
if str(_graph_root) not in sys.path:
    sys.path.insert(0, str(_graph_root))
from graph.artifact_store import save_engineer_log, read_engineer_log, save_design, read_design

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
DEFAULT_MODEL = "anthropic/claude-sonnet-4-6"  # LiteLLM-style slug, model-agnostic via LLM_MODEL env
DEFAULT_TIMEOUT = 900  # 15 minutes
MAX_LOG_CHARS = 5000
WSL_VENV = "~/openhands-venv"
SDK_SCRIPT_DIR = "/tmp/softwarefactory"


# === WSL Helpers ===

def _ensure_wsl_dir(wsl_path: str) -> None:
    subprocess.run(
        ["wsl", "bash", "-lc", f"mkdir -p {wsl_path}"],
        capture_output=True, timeout=10
    )


def _write_wsl_file(wsl_path: str, content: str) -> None:
    """Write content to a file in WSL (base64-encoded to avoid escaping issues)."""
    import base64
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    subprocess.run(
        ["wsl", "bash", "-lc", f"echo '{encoded}' | base64 -d > {wsl_path}"],
        capture_output=True, timeout=30
    )


def _run_wsl_python(wsl_script_path: str, timeout: int = DEFAULT_TIMEOUT) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["wsl", "bash", "-lc",
         f"source {WSL_VENV}/bin/activate && python3 {wsl_script_path} 2>&1"],
        capture_output=True, text=True, timeout=timeout,
        encoding="utf-8", errors="replace"
    )


def _cleanup_wsl_file(wsl_path: str) -> None:
    subprocess.run(
        ["wsl", "bash", "-lc", f"rm -f {wsl_path}"],
        capture_output=True, timeout=5
    )


# === Path Conversion ===

def windows_to_wsl_path(windows_path) -> str:
    """D:\\NewHarness\\... -> /mnt/d/NewHarness/..."""
    path_str = str(windows_path).replace("\\", "/")
    if len(path_str) >= 2 and path_str[1] == ":":
        drive_letter = path_str[0].lower()
        rest_path = path_str[2:]
        return f"/mnt/{drive_letter}{rest_path}"
    return path_str


# === SDK Script Generator ===

SDK_SCRIPT_TEMPLATE = r'''"""OpenHands SDK - SoftwareFactory code generation."""
import json, sys, os, base64
from pathlib import Path

from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.terminal import TerminalTool
from openhands.tools.task_tracker import TaskTrackerTool

wsl_ws = "{wsl_ws}"
Path(wsl_ws).mkdir(parents=True, exist_ok=True)

task_content = base64.b64decode("{task_b64}").decode("utf-8")
Path(f"{wsl_ws}/TASK.md").write_text(task_content)

# Snapshot files BEFORE the agent runs, so we can detect what it actually created.
before_files = {{str(f) for f in Path(wsl_ws).rglob("*") if f.is_file()}}

_base_url = "{base_url}" or None  # empty string -> None (e.g. direct Anthropic, no custom endpoint)
llm = LLM(
    model="{model}",
    api_key="{api_key}",
    base_url=_base_url,
    max_input_tokens=128000,
    max_output_tokens=8192,
)

# tools=[...] is REQUIRED -- without it the agent cannot write files or run
# terminal commands at all, it can only produce text.
agent = Agent(
    llm=llm,
    tools=[
        Tool(name=TerminalTool.name),
        Tool(name=FileEditorTool.name),
        Tool(name=TaskTrackerTool.name),
    ],
)

try:
    conversation = Conversation(agent=agent, workspace=wsl_ws)
    conversation.send_message(task_content)
    conversation.run()

    after_files = {{str(f) for f in Path(wsl_ws).rglob("*") if f.is_file()}}
    new_files = sorted(f for f in (after_files - before_files) if not f.endswith("TASK.md"))

    print("=== RESULT ===")
    print(json.dumps({{
        "status": "completed",
        "files": new_files[:100],
    }}))

except Exception as e:
    print("=== RESULT ===")
    print(json.dumps({{
        "status": "failed",
        "error": str(e)[:2000],
    }}))
    sys.exit(1)
'''


def _build_sdk_script(
    wsl_workspace: str,
    design_doc: str,
    mockup_html: str,
    model: str,
    api_key: str,
    base_url: str = "",
) -> str:
    import base64

    task = (
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
    task_b64 = base64.b64encode(task.encode("utf-8")).decode("ascii")

    return SDK_SCRIPT_TEMPLATE.format(
        wsl_ws=wsl_workspace,
        task_b64=task_b64,
        model=model,
        api_key=api_key,
        base_url=base_url,
    )


# === Main Node Function ===

def engineer_node(state: Any, config: Dict[str, Any]) -> Dict[str, Any]:
    """Generate code using the OpenHands Software Agent SDK via WSL Python.

    Args:
        state: SoftwareFactoryState (Pydantic BaseModel) -- accessed via
            dot-notation (state.design_doc), NOT state["..."] or .get(...).
        config: LangGraph configurable (must contain thread_id)

    Returns:
        State updates: repo_path, engineer_log, status
    """
    logger.info("Starting engineer_node (OpenHands SDK)")

    design_doc = state.design_doc
    mockup_html = state.mockup_html
    thread_id = config.get("configurable", {}).get("thread_id", "default")

    if not design_doc:
        # Fallback: đọc từ Artifact Store
        design_doc = read_design(thread_id)
        if not design_doc:
            logger.warning("No design_doc, using default")
            design_doc = "Generate a simple hello world application."

    workspace_path = SANDBOX_BASE / "workspace" / thread_id
    workspace_path.mkdir(parents=True, exist_ok=True)
    wsl_workspace = windows_to_wsl_path(workspace_path)
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

    script = _build_sdk_script(wsl_workspace, design_doc, mockup_html, model, api_key, base_url)
    script_id = str(uuid.uuid4())[:8]
    _ensure_wsl_dir(SDK_SCRIPT_DIR)
    wsl_script = f"{SDK_SCRIPT_DIR}/oh_{script_id}.py"

    try:
        _write_wsl_file(wsl_script, script)
        logger.info("SDK script written, executing OpenHands SDK...")
        result = _run_wsl_python(wsl_script, timeout=DEFAULT_TIMEOUT)
        stdout = result.stdout.strip()
        logger.info(f"SDK exit: {result.returncode}, output: {len(stdout)} chars")
    except subprocess.TimeoutExpired:
        _cleanup_wsl_file(wsl_script)
        return {
            "repo_path": str(workspace_path),
            "engineer_log": "ERROR: OpenHands SDK timed out after 900s",
            "status": "failed",
        }
    except FileNotFoundError:
        return {
            "repo_path": str(workspace_path),
            "engineer_log": "ERROR: WSL not found. Install WSL.",
            "status": "failed",
        }
    except Exception as e:
        _cleanup_wsl_file(wsl_script)
        return {
            "repo_path": str(workspace_path),
            "engineer_log": f"ERROR: {str(e)}",
            "status": "failed",
        }

    _cleanup_wsl_file(wsl_script)

    # === Parse result ===
    if "=== RESULT ===" in stdout:
        json_part = stdout.split("=== RESULT ===")[-1].strip()
        try:
            data = json.loads(json_part)
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
        except json.JSONDecodeError:
            eng_log = f"OpenHands output:\n{stdout[:2000]}"
            st = "running"
    else:
        eng_log = f"OpenHands output:\n{stdout[:2000]}"
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

    test_state = SoftwareFactoryState(
        design_doc="Create a simple Python web app with Flask",
        mockup_html="<html><body><h1>Hello</h1></body></html>",
    )
    test_config = {"configurable": {"thread_id": "test_engineer_001"}}
    result = engineer_node(test_state, test_config)
    print(json.dumps(result, indent=2, ensure_ascii=False))
