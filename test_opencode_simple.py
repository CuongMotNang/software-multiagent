r"""Test opencode end-to-end: tạo 1 trang HTML Hello World.

Cách chạy:
    cd e:\NewHarness\softwarefactory
    python test_opencode_simple.py

Script sẽ:
1. Đọc .env để lấy NVIDIA_API_KEY
2. Tạo thư mục test e:\NewHarness\test_opencode_ws\
3. git init trong thư mục đó
4. Tạo opencode.json (provider=nvidia, @ai-sdk/openai-compatible)
5. Tạo file instructions.txt
6. Khởi động opencode serve, POST /session + /message
7. Kiểm tra index.html được tạo → in kết quả
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# 1. Load .env
# ---------------------------------------------------------------------------
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

api_key = os.environ.get("NVIDIA_API_KEY", "")
if not api_key:
    print("❌ NVIDIA_API_KEY not found in .env")
    sys.exit(1)
print(f"✅ Loaded NVIDIA_API_KEY (len={len(api_key)})")

# ---------------------------------------------------------------------------
# 2. Tạo thư mục test
# ---------------------------------------------------------------------------
ws = Path(r"e:\NewHarness\test_opencode_ws")
ws.mkdir(parents=True, exist_ok=True)
print(f"✅ Workspace: {ws}")

# ---------------------------------------------------------------------------
# 3. git init (fix opencode stale cwd)
# ---------------------------------------------------------------------------
git_dir = ws / ".git"
if not git_dir.exists():
    subprocess.run(
        ["git", "init", "--quiet"],
        cwd=str(ws),
        check=True,
        timeout=5,
        capture_output=True,
    )
    print("✅ git init done")
else:
    print("✅ git repo already exists")

# ---------------------------------------------------------------------------
# 4. Tạo opencode.json
# ---------------------------------------------------------------------------
config = {
    "$schema": "https://opencode.ai/config.json",
    "provider": {
        "nvidia": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "NVIDIA NIM",
            "options": {
                "baseURL": "https://integrate.api.nvidia.com/v1",
                "apiKey": "{env:NVIDIA_API_KEY}",
            },
            "models": {
                "openai/gpt-oss-120b": {},
            },
        },
    },
}
config_path = ws / "opencode.json"
config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"✅ opencode.json written")

# ---------------------------------------------------------------------------
# 5. Tạo file chỉ dẫn
# ---------------------------------------------------------------------------
instructions_path = ws / "instructions.txt"
instructions_path.write_text(
    "Create a file called index.html with a basic HTML5 page that displays "
    "the text 'Hello World' in the browser. Write the file now.",
    encoding="utf-8",
)
print(f"✅ instructions.txt written")

# ---------------------------------------------------------------------------
# 6. Khởi động opencode serve
# ---------------------------------------------------------------------------
port = 4099
opencode_exe = shutil.which("opencode")
if not opencode_exe:
    print("❌ opencode not found on PATH")
    sys.exit(1)

print(f"Starting opencode serve on port {port} (cwd={ws}) ...")
proc = subprocess.Popen(
    [opencode_exe, "serve", "--port", str(port), "--hostname", "127.0.0.1"],
    cwd=str(ws),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)

try:
    # Health check
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 20
    ready = False
    with httpx.Client(timeout=3) as probe:
        while time.time() < deadline:
            try:
                r = probe.get(f"{base_url}/global/health")
                if r.status_code == 200:
                    ready = True
                    break
            except httpx.TransportError:
                pass
            time.sleep(0.5)
    if not ready:
        print("❌ opencode serve did not start in time")
        sys.exit(1)
    print("✅ opencode serve is up")

    time.sleep(2)

    with httpx.Client(timeout=120, base_url=base_url) as client:
        # Create session
        resp = client.post("/session", json={
            "permission": [{"permission": "*", "pattern": "*", "action": "allow"}]
        })
        resp.raise_for_status()
        session_id = resp.json()["id"]
        print(f"✅ Session: {session_id}")

        # Send message
        instructions = instructions_path.read_text(encoding="utf-8")
        resp = client.post(f"/session/{session_id}/message", json={
            "model": {"providerID": "nvidia", "modelID": "openai/gpt-oss-120b"},
            "parts": [{"type": "text", "text": instructions}],
        })
        resp.raise_for_status()
        data = resp.json()

        info = data.get("info", {})
        tokens = info.get("tokens", {}) or {}
        print(f"✅ /message done  | tokens in={tokens.get('input',0)} out={tokens.get('output',0)}")

        if info.get("error"):
            print(f"❌ Agent error: {info['error']}")
            sys.exit(1)

        # Extract text from parts
        for part in data.get("parts", []):
            if part.get("type") == "text":
                print(f"   Agent says: {part['text'][:200]}")

finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()

# ---------------------------------------------------------------------------
# 7. Kiểm tra index.html
# ---------------------------------------------------------------------------
html_path = ws / "index.html"
if html_path.exists():
    content = html_path.read_text(encoding="utf-8")
    print(f"\n🎉 SUCCESS! index.html created ({len(content)} bytes):")
    print("-" * 50)
    print(content[:500])
    print("-" * 50)
else:
    print(f"\n❌ FAIL! index.html not found in {ws}")
    print("Files in workspace:")
    for f in sorted(ws.iterdir()):
        print(f"  {f.name}")
    sys.exit(1)