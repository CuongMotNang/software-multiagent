"""Serve artifact files (mockup screenshots, HTML) for React frontend.

Chạy song song với ``langgraph dev`` để React có thể load ảnh PNG từ
``/artifacts/{thread_id}/mockup_versions/v{version}/screenshots/screen_*.png``
qua proxy trong vite.config.ts.

Usage:
    python server/static_server.py
    # Listen on http://0.0.0.0:3001
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn

SANDBOX_WORKSPACE = Path(__file__).resolve().parent.parent / "sandbox" / "workspace"

app = FastAPI(title="SoftwareFactory Artifact Server")

# Mount toàn bộ sandbox/workspace dưới /artifacts
if SANDBOX_WORKSPACE.exists():
    app.mount("/artifacts", StaticFiles(directory=str(SANDBOX_WORKSPACE)), name="artifacts")
else:
    print(f"[static_server] WARNING: sandbox/workspace not found at {SANDBOX_WORKSPACE}")


@app.get("/health")
async def health():
    return {"status": "ok", "static_dir": str(SANDBOX_WORKSPACE)}


if __name__ == "__main__":
    print(f"[static_server] Serving {SANDBOX_WORKSPACE} on http://0.0.0.0:3001")
    uvicorn.run(app, host="0.0.0.0", port=3001)