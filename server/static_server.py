"""Serve artifact files (mockup screenshots, HTML) for React frontend.

Chạy song song với ``langgraph dev`` để React có thể load ảnh PNG từ
``/artifacts/{thread_id}/mockup_versions/v{version}/screenshots/screen_*.png``
qua proxy trong vite.config.ts. Ngoài ra còn route POST ``/repo/.../mockup/screens/{slug}``
để Puck editor ghi UI JSON chỉnh tay vào repo Git.

Usage:
    python server/static_server.py
    # Listen on http://0.0.0.0:3001
"""

import json
import sys
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
import uvicorn

# Cho phép import package "graph" khi chạy trực tiếp `python server/static_server.py`
# (không cài package, chỉ chạy từ nguồn) — cần thêm root repo vào sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import graph.repo_store as repo_store  # noqa: E402  (import sau khi chỉnh sys.path)
from graph.repo_store import read_design_tokens, save_mockup_screens, screenshot_dir  # noqa: E402

# ── Transitional (Bước 1): Puck → GrapesJS ──
# ui_node.py không còn import UIScreen/render_screen_to_html nữa (đã chuyển
# sang sinh HTML trực tiếp). static_server vẫn import để route POST cũ
# không crash — nhưng bọc try-except để server vẫn khởi động được nếu các
# module này bị xóa sau này.
try:
    from graph.schemas import DesignTokens, UIScreen  # noqa: E402
    from graph.ui_json_renderer import render_screen_to_html  # noqa: E402
    _PUCK_AVAILABLE = True
except ImportError:
    _PUCK_AVAILABLE = False

SANDBOX_WORKSPACE = Path(__file__).resolve().parent.parent / "sandbox" / "workspace"
# Lưu ý: Dữ liệu projects thực tế được pipeline ghi vào projects_data/ (qua volume mount)
# chứ không phải projects/ — projects/ là thư mục ảo, bị .gitignore bỏ qua
# và hiện tại trống. projects_data/ chứa nội dung thật từ container.
PROJECTS_ROOT = Path(__file__).resolve().parent.parent / "projects_data"

SCREENSHOT_DIR_NAME = "mockup_screenshots_xem_thu"

app = FastAPI(title="SoftwareFactory Artifact Server")

# Mount toàn bộ sandbox/workspace dưới /artifacts (screenshot PNG, build output — không track git)
if SANDBOX_WORKSPACE.exists():
    app.mount("/artifacts", StaticFiles(directory=str(SANDBOX_WORKSPACE)), name="artifacts")
else:
    print(f"[static_server] WARNING: sandbox/workspace not found at {SANDBOX_WORKSPACE}")

# Mount toàn bộ projects/ dưới /repo — nội dung PRD/design/mockup thật (git-tracked, xem repo_store.py)
PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)

# QUAN TRỌNG: repo_store.py mặc định tính PROJECTS_ROOT = <repo>/projects — đúng
# khi chạy BÊN TRONG container langgraph-api, nơi "projects/" được bind-mount
# sang host "projects_data/" (xem langgraph-override.yml). static_server.py lại
# chạy TRỰC TIẾP trên host, song song với container đó (không phải bên trong),
# nên nếu không ghi đè, các hàm save_mockup_screens()/read_design_tokens() của
# repo_store sẽ đọc/ghi vào 1 thư mục "projects/" hoàn toàn khác — không phải
# nơi StaticFiles ở dưới đang serve qua /repo. Ghi đè thẳng để cả hai luôn trỏ
# về cùng 1 thư mục thật trên host.
repo_store.PROJECTS_ROOT = PROJECTS_ROOT


def _validate_slug_like(value: str, field_name: str) -> None:
    if "/" in value or "\\" in value or ".." in value:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}")


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
    """Trả về cây thư mục (JSON) của workspace 1 thread — screenshot/build
    output KHÔNG track git (xem /tree/project/{project_id} cho nội dung
    PRD/design/mockup thật)."""
    # Chống path traversal: thread_id không được chứa dấu / \ hoặc "..".
    if "/" in thread_id or "\\" in thread_id or ".." in thread_id:
        raise HTTPException(status_code=400, detail="Invalid thread_id")

    root = SANDBOX_WORKSPACE / thread_id
    if not root.exists() or not root.is_dir():
        raise HTTPException(status_code=404, detail=f"Thread workspace not found: {thread_id}")

    return _build_tree(root)


@app.get("/tree/project/{project_id}")
async def get_project_tree(project_id: str):
    """Cây thư mục (JSON) của 1 project repo — nội dung PRD/design/mockup
    thật, track git qua repo_store.py. project_id hiện = thread_id đầu
    tiên của project (xem quyết định trong ke-hoach-cai-tien-pipeline.md,
    Giai đoạn 0.2)."""
    if "/" in project_id or "\\" in project_id or ".." in project_id:
        raise HTTPException(status_code=400, detail="Invalid project_id")

    root = PROJECTS_ROOT / project_id
    if not root.exists() or not root.is_dir():
        raise HTTPException(status_code=404, detail=f"Project repo not found: {project_id}")

    return _build_tree(root)


@app.get("/health")
async def health():
    return {"status": "ok", "static_dir": str(SANDBOX_WORKSPACE)}


# ---------------------------------------------------------------------------
# LƯU Ý THỨ TỰ: route POST cụ thể này PHẢI được đăng ký TRƯỚC dòng
# `app.mount("/repo", ...)` bên dưới. Starlette match route theo đúng thứ tự
# được thêm vào router, và 1 Mount khớp theo PREFIX đường dẫn bất kể HTTP
# method — nếu mount("/repo") đứng trước, mọi request (kể cả POST) vào
# /repo/... sẽ bị StaticFiles "nuốt" trước (trả 405, vì StaticFiles chỉ hiểu
# GET/HEAD) và route bên dưới không bao giờ được gọi tới.
# ---------------------------------------------------------------------------
@app.post("/repo/{project_id}/mockup/screens/{slug}")
async def save_mockup_screen(project_id: str, slug: str, screen: dict = Body(...)):
    """[DEPRECATED — Bước 1] Lưu 1 màn hình UI JSON đã sửa tay qua Puck editor.

    Route này sẽ bị xóa hoặc thay thế bằng route save HTML trực tiếp ở Bước 2
    (chuyển Puck → GrapesJS). Hiện tại vẫn hoạt động nếu _PUCK_AVAILABLE=True,
    nhưng không còn được gọi từ frontend mới (MockupGrapesEditor).
    """
    if not _PUCK_AVAILABLE:
        raise HTTPException(status_code=410, detail="Puck editor đã bị deprecated — dùng GrapesJS thay thế (Bước 1-2)")

    _validate_slug_like(project_id, "project_id")
    _validate_slug_like(slug, "slug")

    try:
        validated = UIScreen.model_validate(screen)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"UI JSON không hợp lệ: {e}")

    # slug trên URL luôn là nguồn sự thật cho tên file — tránh payload.screen
    # bị lệch tên khiến ghi nhầm file khác.
    if validated.screen != slug:
        validated = validated.model_copy(update={"screen": slug})

    content = json.dumps(validated.model_dump(), indent=2, ensure_ascii=False)
    try:
        save_mockup_screens(project_id, [{"filename": f"{slug}.json", "content": content}])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lưu git thất bại: {e}")

    preview_warning: str | None = None
    try:
        tokens_raw = read_design_tokens(project_id)
        if not tokens_raw:
            raise RuntimeError("design_tokens.json chưa tồn tại cho project này — chưa render lại được preview")
        tokens = DesignTokens.model_validate(json.loads(tokens_raw))
        html = render_screen_to_html(validated, tokens)

        shot_dir = screenshot_dir(project_id)
        preview_html_path = shot_dir / f"{slug}.preview.html"
        preview_html_path.write_text(html, encoding="utf-8")

        from graph.mockup_renderer import render_html_to_png  # import trễ — tránh phụ thuộc Playwright lúc khởi động server nếu chưa cần

        png_path = shot_dir / f"{slug}.preview.png"
        render_html_to_png(preview_html_path, png_path)
    except Exception as e:
        preview_warning = str(e)

    return {
        "ok": True,
        "screen": validated.screen,
        "deprecated": True,
        "preview_regenerated": preview_warning is None,
        "preview_warning": preview_warning,
    }


app.mount("/repo", StaticFiles(directory=str(PROJECTS_ROOT)), name="repo")


if __name__ == "__main__":
    print(f"[static_server] Serving {SANDBOX_WORKSPACE} on http://0.0.0.0:3001")
    uvicorn.run(app, host="0.0.0.0", port=3001)