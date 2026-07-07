"""Serve artifact files (mockup screenshots, HTML) for React frontend.

Chạy song song với ``langgraph dev`` để React có thể load ảnh PNG từ
``/artifacts/{thread_id}/mockup_versions/v{version}/screenshots/screen_*.png``
qua proxy trong vite.config.ts.

Usage:
    python server/static_server.py
    # Listen on http://0.0.0.0:3001
"""

from fastapi import FastAPI, HTTPException
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


# Các thư mục không cần hiển thị trên file tree (rác/build artifact, không phải code)
_EXCLUDE_DIRS = {"__pycache__", "node_modules", ".git", "venv", ".venv", ".pytest_cache", ".mypy_cache"}


def _build_tree(path: Path, rel: str = "") -> dict:
    node: dict = {"name": path.name, "type": "dir", "path": rel, "children": []}
    try:
        entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except (PermissionError, OSError):
        return node

    for entry in entries:
        if entry.name in _EXCLUDE_DIRS:
            continue
        entry_rel = f"{rel}/{entry.name}" if rel else entry.name
        if entry.is_dir():
            node["children"].append(_build_tree(entry, entry_rel))
        else:
            try:
                size = entry.stat().st_size
            except OSError:
                size = None
            node["children"].append(
                {"name": entry.name, "type": "file", "path": entry_rel, "size": size}
            )
    return node


@app.get("/tree/{thread_id}")
async def get_tree(thread_id: str):
    """Trả về cây thư mục (JSON) của workspace 1 thread, dùng cho file browser
    kiểu GitHub ở frontend.
    """
    # Chống path traversal: thread_id không được chứa dấu / \ hoặc "..".
    # thread_id đến trực tiếp từ URL do client gửi lên, không kiểm tra sẽ
    # cho phép đọc bất kỳ file nào ngoài sandbox/workspace.
    if "/" in thread_id or "\\" in thread_id or ".." in thread_id:
        raise HTTPException(status_code=400, detail="Invalid thread_id")

    root = SANDBOX_WORKSPACE / thread_id
    if not root.exists() or not root.is_dir():
        raise HTTPException(status_code=404, detail=f"Thread workspace not found: {thread_id}")

    return _build_tree(root)


@app.get("/health")
async def health():
    return {"status": "ok", "static_dir": str(SANDBOX_WORKSPACE)}


if __name__ == "__main__":
    print(f"[static_server] Serving {SANDBOX_WORKSPACE} on http://0.0.0.0:3001")
    uvicorn.run(app, host="0.0.0.0", port=3001)