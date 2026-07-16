"""Agent Runtime — tầng trung gian giữa graph (LangGraph node) và SDK agent thật.

Kiến trúc 3 tầng đã thống nhất:
    TẦNG GRAPH (ba_node.py...) -> TẦNG AGENT RUNTIME (file này) -> TẦNG SDK (OpenHands)

Node chỉ gọi run_agent(runtime_name, task, cfg), không biết gì về OpenHands SDK bên
trong — đổi runtime (vd sang Claude Code sau này) chỉ cần thêm 1 hàm run_xxx() mới và
đăng ký vào RUNTIMES, không sửa node.
"""

from __future__ import annotations
import os
import logging
from pathlib import Path
from typing import Any, Callable, Literal, TypedDict

logger = logging.getLogger(__name__)


class AgentTask(TypedDict, total=False):
    instructions: str
    workspace_path: Path
    output_file: str


class AgentResult(TypedDict):
    status: Literal["completed", "failed"]
    output: str
    log: str
    prompt_tokens: int
    completion_tokens: int
    model: str


def _resolve_model(cfg) -> tuple[str, str]:
    raw = (cfg.get("model") or os.environ.get("BA_LLM_MODEL", "")).strip()
    if not raw:
        raw = os.environ.get("NVIDIA_MODEL", "").strip()
    if not raw:
        raw = "openai/gpt-oss-120b"
    if "/" in raw:
        parts = raw.split("/", 1)
        provider, model_id_part = parts[0].strip(), parts[1].strip()
    else:
        provider = "openai"
        model_id_part = raw.strip()
    base_url = (
        cfg.get("base_url")
        or os.environ.get("BA_LLM_BASE_URL", "")
        or os.environ.get("NVIDIA_API_BASE", "")
    )
    if provider == "openai" and base_url and "nvidia" in base_url.lower():
        # NVIDIA NIM dùng @ai-sdk/openai-compatible → remap provider 'openai' -> 'nvidia'.
        # QUAN TRỌNG: provider key trong opencode.json PHẢI là "nvidia" (không phải
        # "openai") để khớp với providerID gửi trong /message body. Tham chiếu
        # test_opencode_simple.py (đã verified OK): provider="nvidia", apiKey="{env:...}".
        logger.info(
            "[agent_runtime] NVIDIA NIM detected (base_url=%s) — remapping provider '%s' -> 'nvidia'",
            base_url, provider,
        )
        provider = "nvidia"
        model_id = f"openai/{model_id_part}"
    else:
        model_id = model_id_part
    logger.debug("[agent_runtime] resolved model: provider=%s modelID=%s", provider, model_id)
    return provider, model_id


def _ensure_opencode_config(workspace_path: Path, cfg: dict[str, Any]) -> None:
    """Ghi opencode.json vào workspace với apiKey/baseURL từ cfg."""
    config_path = workspace_path / "opencode.json"
    if config_path.exists():
        return
    provider, model_id = _resolve_model(cfg)
    base_url = cfg.get("base_url") or os.environ.get("BA_LLM_BASE_URL") or os.environ.get("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")
    api_key = cfg.get("api_key") or os.environ.get("BA_LLM_API_KEY") or os.environ.get("NVIDIA_API_KEY", "")
    # opencode hỗ trợ tham chiếu env var qua cú pháp "{env:VAR}" — tránh hardcode key
    # vào file (an toàn hơn, khớp với test_opencode_simple.py đã verified).
    # Ưu tiên env var thật khi có, fallback về giá trị cfg (dùng cho override riêng).
    env_key_name = "NVIDIA_API_KEY" if os.environ.get("NVIDIA_API_KEY") else None
    if env_key_name:
        api_key_ref = f"{{env:{env_key_name}}}"
    else:
        api_key_ref = api_key
    import json
    config = {
        "$schema": "https://opencode.ai/config.json",
        "provider": {
            provider: {
                "npm": "@ai-sdk/openai-compatible",
                "name": "NVIDIA NIM",
                "options": {"baseURL": base_url, "apiKey": api_key_ref},
                "models": {model_id: {}},
            },
        },
    }
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("[agent_runtime] wrote opencode.json to %s (provider=%s)", config_path, provider)


def _read_proc_stdout(proc) -> str:
    """Đọc stdout không chặn (tối đa 4KB)."""
    if not proc or not proc.stdout:
        return ""
    try:
        raw = proc.stdout.read(4096)
        return raw.decode("utf-8", errors="replace") if raw else ""
    except Exception:
        return ""


# ── Port counter: mỗi lần gọi run_opencode_agent dùng 1 port riêng, tránh xung đột
# khi node trước chưa kịp giải phóng port mà node sau đã khởi động opencode mới.
_port_counter: int = 0
_BASE_PORT: int = 4100


def _next_port() -> int:
    global _port_counter
    _port_counter += 1
    return _BASE_PORT + _port_counter


def run_opencode_agent(task: AgentTask, cfg: dict[str, Any]) -> AgentResult:
    import shutil, subprocess, time
    import httpx

    workspace_path: Path = task["workspace_path"]
    workspace_path.mkdir(parents=True, exist_ok=True)
    output_file = task.get("output_file") or None
    port = cfg.get("port") if cfg.get("port") and cfg["port"] != 4096 else _next_port()
    base_url = f"http://127.0.0.1:{port}"

    _ensure_opencode_config(workspace_path, cfg)

    # ── git init ──
    import subprocess as _sp
    if not (workspace_path / ".git").exists():
        try:
            _sp.run(["git", "init", "--quiet"], cwd=str(workspace_path), check=True, timeout=5, capture_output=True)
            logger.info("[agent_runtime] git init in %s", workspace_path)
        except Exception as e:
            logger.warning("[agent_runtime] git init failed: %s", e)

    # ── Tìm opencode binary (dùng shutil.which giống test_opencode_simple.py) ──
    opencode_exe = shutil.which("opencode")
    if opencode_exe and opencode_exe.lower().endswith(".ps1"):
        opencode_exe = None
    if opencode_exe:
        logger.info("[agent_runtime] using opencode: %s", opencode_exe)

    # Fallback: nếu không tìm thấy, dùng npx opencode hoặc tìm trong npm global
    _opcode_args = []
    if not opencode_exe:
        npx_path = shutil.which("npx")
        if npx_path:
            opencode_exe = npx_path
            _opcode_args = ["opencode"]
            logger.info("[agent_runtime] using npx opencode (fallback): %s", npx_path)
        else:
            npm_exe = Path(os.environ.get("APPDATA", "")) / "npm" / "node_modules" / "opencode-ai" / "bin" / "opencode.exe"
            if npm_exe.exists():
                opencode_exe = str(npm_exe)
                logger.info("[agent_runtime] using opencode from npm global: %s", opencode_exe)
            else:
                return AgentResult(status="failed", output="", log="opencode not found on PATH and npx not available — install via `npm i -g opencode-ai`", prompt_tokens=0, completion_tokens=0, model="")

    # ── Start opencode serve (LUÔN start Popen mới với CWD = workspace_path) ──
    # Pass current environment variables so OpenCode can resolve {env:VAR_NAME}
    proc_env = dict(os.environ)
    proc = subprocess.Popen(
        [opencode_exe] + _opcode_args + ["serve", "--port", str(port), "--hostname", "127.0.0.1"],
        cwd=str(workspace_path), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        env=proc_env,
    )
    deadline = time.time() + cfg.get("startup_timeout", 20)
    with httpx.Client(timeout=3) as probe:
        while time.time() < deadline:
            try:
                if probe.get(f"{base_url}/global/health").status_code == 200:
                    break
            except httpx.TransportError:
                pass
            time.sleep(0.5)
        else:
            log = _read_proc_stdout(proc)
            proc.terminate()
            return AgentResult(status="failed", output="", log=f"opencode serve timeout | log: {log[:1000]}", prompt_tokens=0, completion_tokens=0, model="")
    time.sleep(2)

    # ── Session + Message ──
    try:
        with httpx.Client(timeout=cfg.get("timeout", 600), base_url=base_url) as client:
            # Tạo session — truyền directory để opencode set đúng CWD
            # (field này có hiệu lực khi tạo session mới, dù docstring cũ nói không)
            session_payload = {
                "permission": [{"permission": "*", "pattern": "*", "action": "allow"}],
                "directory": str(workspace_path),
            }
            resp = client.post("/session", json=session_payload)
            if resp.status_code >= 400:
                return AgentResult(status="failed", output="", log=f"/session {resp.status_code}: {resp.text[:500]}", prompt_tokens=0, completion_tokens=0, model="")
            session_id = resp.json()["id"]

            provider_id, model_id = _resolve_model(cfg)
            instructions = task["instructions"].replace("\\", "/")

            resp = client.post(f"/session/{session_id}/message", json={
                "model": {"providerID": provider_id, "modelID": model_id},
                "parts": [{"type": "text", "text": instructions}],
            })
            if resp.status_code >= 400:
                return AgentResult(status="failed", output="", log=f"/message {resp.status_code}: {resp.text[:500]}", prompt_tokens=0, completion_tokens=0, model="")
            data = resp.json()

        info = data.get("info", {})
        model_id = info.get("modelID", "")
        tokens = info.get("tokens", {}) or {}
        pt = tokens.get("input", 0)
        ct = tokens.get("output", 0)

        if info.get("error"):
            return AgentResult(status="failed", output="", log=f"OpenCode error: {info['error']}", prompt_tokens=pt, completion_tokens=ct, model=model_id)

        # QUAN TRỌNG: POST /session/{id}/message của OpenCode KHÔNG đảm bảo
        # đợi agent thật sự chạy xong tool-call/ghi file trước khi trả HTTP
        # response — đây là hạn chế đã biết của chính OpenCode server (xem
        # sst/opencode#2168, #3075: "empty response... should I be polling
        # GET /session/{id}/messages?"). Trước đây code coi response ban đầu
        # là đủ ("output_file is None -> return completed ngay") -> với task
        # dài (nhiều tool-call, nhiều file, VD bmad-ux) trả về SỚM khi agent
        # còn đang chạy, dẫn tới output rỗng + file chưa kịp ghi.
        #
        # Fix: poll GET /session/{id}/messages tới khi message cuối cùng
        # KHÔNG đổi nữa qua 2 lần poll liên tiếp (heuristic "đã ổn định" —
        # OpenCode không có field "completed" tường minh trong response này
        # theo báo cáo cộng đồng, nên dùng stabilization thay vì tin field
        # cụ thể nào).
        final_text = ""
        # Giới hạn riêng cho vòng poll này, KHÔNG dùng nguyên cfg["timeout"]
        # (mặc định 600s) — nếu endpoint /messages sai đường dẫn/schema so
        # với bản OpenCode đang cài (từng có report khác nhau giữa version),
        # tránh việc MỌI lần gọi đều bị treo tới hết 600s một cách vô ích.
        poll_timeout_s = min(cfg.get("timeout", 600), 180)
        poll_deadline = time.time() + poll_timeout_s
        last_snapshot = None
        stable_count = 0
        empty_poll_count = 0
        while time.time() < poll_deadline:
            try:
                msgs_resp = httpx.get(f"{base_url}/session/{session_id}/messages", timeout=10)
                msgs = msgs_resp.json() if msgs_resp.status_code == 200 else []
            except (httpx.TransportError, ValueError):
                msgs = []

            assistant_msgs = [m for m in msgs if (m.get("info") or m).get("role") == "assistant"]
            if not assistant_msgs:
                empty_poll_count += 1
                if empty_poll_count >= 5:
                    # 15s liên tục không thấy message nào -> nhiều khả năng
                    # endpoint/schema không khớp bản OpenCode này, không
                    # phải agent còn đang chạy. Dừng sớm, không đợi hết
                    # poll_timeout_s vô ích — node vẫn tự fallback quét file
                    # trong workspace như trước.
                    logger.warning(
                        "[agent_runtime] Không đọc được message nào từ "
                        "/session/%s/messages sau %d lần thử — có thể "
                        "endpoint/schema khác bản OpenCode đang cài. Dừng "
                        "sớm, dựa vào việc node tự quét file trong workspace.",
                        session_id, empty_poll_count,
                    )
                    break
                time.sleep(3)
                continue
            empty_poll_count = 0
            last_msg = assistant_msgs[-1]
            parts = last_msg.get("parts", [])
            text_parts = [p.get("text", "") for p in parts if p.get("type") == "text"]
            snapshot = "".join(text_parts)
            has_pending_tool = any(
                p.get("type") == "tool" and p.get("state", {}).get("status") not in ("completed", "error")
                for p in parts
            )
            if snapshot == last_snapshot and not has_pending_tool and snapshot:
                stable_count += 1
                if stable_count >= 2:
                    final_text = snapshot
                    break
            else:
                stable_count = 0
            last_snapshot = snapshot
            time.sleep(3)
        else:
            logger.warning("[agent_runtime] Timeout chờ OpenCode session ổn định, dùng snapshot cuối cùng đọc được")
            final_text = last_snapshot or ""

        # Nếu không yêu cầu output_file cụ thể (None) → node tự đọc file từ
        # workspace, nhưng giờ đã ĐỢI session ổn định thật sự nên file có
        # nhiều khả năng đã tồn tại khi node đi check.
        if output_file is None:
            return AgentResult(status="completed", output=final_text, log="ok", prompt_tokens=pt, completion_tokens=ct, model=model_id)

        output_path = workspace_path / output_file
        deadline = time.time() + cfg.get("output_timeout", 120)
        while time.time() < deadline:
            if output_path.exists():
                break
            time.sleep(2)
        if not output_path.exists():
            return AgentResult(status="failed", output="", log=f"Agent không tạo ra file {output_file}", prompt_tokens=pt, completion_tokens=ct, model=model_id)

        return AgentResult(status="completed", output=output_path.read_text(encoding="utf-8"), log="ok", prompt_tokens=pt, completion_tokens=ct, model=model_id)
    finally:
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


RUNTIMES: dict[str, Callable[[AgentTask, dict[str, Any]], AgentResult]] = {
    "opencode": run_opencode_agent,
}


def run_agent(runtime_name: str, task: AgentTask, cfg: dict[str, Any]) -> AgentResult:
    if runtime_name not in RUNTIMES:
        raise ValueError(f"Unknown agent runtime: {runtime_name!r}. Có sẵn: {list(RUNTIMES)}")
    return RUNTIMES[runtime_name](task, cfg)