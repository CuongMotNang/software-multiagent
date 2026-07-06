"""
UINode: Generate HTML mockup screens & render to PNG.
"""

import re
from pathlib import Path
from typing import Any
from datetime import datetime

from langchain_core.runnables import RunnableConfig

from graph.state import SoftwareFactoryState, MAX_HISTORY_VERSIONS
from graph.llm import llm_factory, LLMResponse
from graph.stats_utils import count_rejects

# Mapping node_name → gate_name để tính reject_count
_NODE_GATES = {
    "ba": None,
    "prd": "gate_prd",
    "design": "gate_design",
    "ui": "gate_mockup",
}

CUR_DIR = Path(__file__).parent.parent.resolve()
PROMPT_DIR = CUR_DIR / ".." / "prompts"
SANDBOX = Path(__file__).resolve().parent.parent.parent / "sandbox" / "workspace"

# Chỉ khớp đúng format mà design_system prompt yêu cầu:
#   {số_thứ_tự}_{tên_file}|{tên_hiển_thị}   ví dụ: 01_login|Đăng nhập
# KHÔNG dùng "bất kỳ dòng nào có dấu |" vì design_doc còn chứa mermaid
# diagrams (vd: `A -->|Open| B`) và nhiều bảng markdown khác (ERD, Data
# Dictionary, Exception table...) cũng dùng ký tự "|" nhưng không phải
# là màn hình -- bắt nhầm dòng đó sẽ ra slug rác kiểu "D -->" và làm
# path.write_text() ném OSError trên Windows (ký tự '>' không hợp lệ).
_SCREEN_LINE_RE = re.compile(
    r'^\s*\|?\s*(\d{1,2}_[a-zA-Z0-9_]+)\s*\|\s*([^|]+?)\s*\|?\s*$'
)

# Ký tự không hợp lệ trong tên file trên Windows/macOS/Linux.
_INVALID_FS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _sanitize_slug(slug: str) -> str:
    """Đảm bảo slug an toàn để làm tên file trên mọi OS (đặc biệt Windows)."""
    slug = slug.strip().strip(". ")
    slug = _INVALID_FS_CHARS.sub("", slug)
    return slug


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_prompt(sub: str, version: str | None = None) -> str:
    if version:
        p = PROMPT_DIR / "versions" / f"{version}_{sub}"
    else:
        p = PROMPT_DIR / "system" / sub
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _ask_llm(prompt: str, *, max_tokens=20000, **kwargs) -> LLMResponse:
    import os
    provider_name = os.getenv("UI_PROVIDER", None)
    llm = llm_factory(provider_name)
    llm_response = llm.call(
        system_prompt="",
        user_prompt=prompt,
        temperature=kwargs.get("temperature", 0.3),
        max_tokens=max_tokens,
    )
    return llm_response


# ---------------------------------------------------------------------------
# Phase 1 – list screens from design_doc
# ---------------------------------------------------------------------------

def _list_screens(state: SoftwareFactoryState) -> list[tuple[str, str]]:
    """Parse design_doc để lấy danh sách màn hình (slug, label).

    Chỉ nhận đúng format `NN_ten_file|Tên hiển thị` theo convention của
    design_system prompt (mục "# 3. UI SCREENS"). design_doc còn chứa
    mermaid diagrams + nhiều bảng markdown khác (ERD, Data Dictionary,
    Exception table...) — những dòng đó cũng có "|" nhưng KHÔNG phải
    màn hình, nên không được match bừa.
    """
    design = state.design_doc or ""
    screens: list[tuple[str, str]] = []
    for line in design.splitlines():
        m = _SCREEN_LINE_RE.match(line.strip())
        if not m:
            continue
        slug = _sanitize_slug(m.group(1))
        label = m.group(2).strip()
        if slug and label:
            screens.append((slug, label))
    return screens


def _list_screens_via_llm(state: SoftwareFactoryState) -> list[tuple[str, str]]:
    """Fallback: design_doc đôi khi KHÔNG viết mục UI SCREENS theo đúng
    format (LLM bỏ sót dù đã được yêu cầu trong design_system prompt).
    Khi đó gọi riêng 1 lần LLM với prompt `ui_screens_list.txt` (đã có
    sẵn trong repo nhưng trước giờ chưa được dùng tới) để LLM liệt kê lại
    danh sách màn hình từ design_doc, đảm bảo output đúng format.
    """
    system_prompt = _read_prompt("ui_screens_list.txt")
    if not system_prompt:
        return []

    design = state.design_doc or ""
    prompt = f"{system_prompt}\n\n## TÀI LIỆU THIẾT KẾ\n\n{design[:6000]}"
    raw = _ask_llm(prompt, max_tokens=1024)

    screens: list[tuple[str, str]] = []
    for line in raw.splitlines():
        m = _SCREEN_LINE_RE.match(line.strip())
        if not m:
            continue
        slug = _sanitize_slug(m.group(1))
        label = m.group(2).strip()
        if slug and label:
            screens.append((slug, label))
    return screens



# ---------------------------------------------------------------------------
# Phase 2 – generate one HTML per screen
# ---------------------------------------------------------------------------

def _generate_screen_html(screen_slug: str, screen_label: str,
                            design: str, prd: str, requirements: str,
                            version: int, llm_responses: list[LLMResponse]) -> str:
    base_prompt = _read_prompt("ui_system.txt")
    screen_prompt = _read_prompt("ui_screen_detail.txt", version=f"v{version}")
    if not screen_prompt:
        screen_prompt = (
            f"Tạo file HTML hoàn chỉnh cho màn hình: {screen_slug} - {screen_label}\n"
            "Yêu cầu:\n"
            "- Style inline hoặc <style> trong <head>\n"
            "- Responsive, đẹp, chuyên nghiệp\n"
            "- CHỈ trả về code HTML, không có text khác\n"
        )

    prd_summary = prd[:2000] if prd else ""
    req_summary = requirements[:2000] if requirements else ""

    user_msg = f"""
{screen_prompt}

THIẾT KẾ TỔNG THỂ:
{design[:3000] or 'Không có thiết kế chi tiết'}

YÊU CẦU CHỨC NĂNG:
{prd_summary}

SCREEN: {screen_slug} | {screen_label}

QUAN TRỌNG — GHI ĐÈ HƯỚNG DẪN Ở TRÊN:
Lần này CHỈ tạo DUY NHẤT 1 màn hình "{screen_slug}" ở trên.
KHÔNG dùng định dạng ===FILE:...=== (đó là để gộp nhiều màn hình, không áp dụng ở đây).
KHÔNG tạo thêm màn hình nào khác.
CHỈ trả về đúng 1 khối HTML hoàn chỉnh, bắt đầu bằng <!DOCTYPE html>, không có text giải thích nào khác.
"""
    prompt = f"{base_prompt}\n\n{user_msg}"
    llm_response = _ask_llm(prompt, max_tokens=4096)
    llm_responses.append(llm_response)  # Lưu response để cộng dồn token
    html = llm_response.content or ""
    html = _extract_single_html(html)
    return html

def _extract_single_html(raw: str) -> str:
    """Safety-net: nếu LLM vẫn lỡ trả về nhiều file theo marker
    ``===FILE:xxx.html===`` (do system prompt ui_system.txt vốn được viết
    cho chế độ gộp nhiều màn hình), chỉ lấy đúng 1 block HTML đầu tiên
    thay vì lưu nguyên văn cả cục (kèm marker) làm hỏng file.
    """
    if "===FILE:" not in raw:
        return raw.strip()

    parts = re.split(r'===FILE:[^=]*===', raw)
    # phần tử đầu tiên (trước marker đầu) thường rỗng/không liên quan
    for part in parts:
        part = part.strip()
        if part:
            return part
    return raw.strip()


def _save_html(html: str, dir: Path, name: str) -> Path:
    dir.mkdir(parents=True, exist_ok=True)
    path = dir / f"{name}.html"
    path.write_text(html, encoding="utf-8")
    return path

# ---------------------------------------------------------------------------
# Phase 3 – capture screenshots
# ---------------------------------------------------------------------------

def _capture_screens_to(html_paths: list[Path], output_dir: Path) -> list[Path]:
    """Capture each HTML file to PNG in output_dir."""
    from graph.mockup_renderer import render_html_to_png

    png_paths: list[Path] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for html_path in html_paths:
        png_name = html_path.stem + ".png"
        png_path = output_dir / png_name
        try:
            render_html_to_png(html_path, png_path)
            png_paths.append(png_path)
        except Exception as e:
            print(f"  ⚠️ PNG failed for {html_path.name}: {e}")
    return png_paths

# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def ui_node(state: SoftwareFactoryState, config: RunnableConfig | None = None, **kwargs) -> dict[str, Any]:
    print("\n🚀 UINode: generating mockup screens...")

    # Lấy thread_id từ config (giống ba_node/prd_node/design_node/gate_mockup).
    # PHẢI type là RunnableConfig (không phải dict) để LangGraph tự inject
    # config thật -- nếu type sai, LangGraph không nhận diện được tham số
    # này là config nên sẽ không truyền vào, và thread_id lại rơi về "default".
    thread_id = "default"
    if config:
        configurable = config.get("configurable", {}) or {}
        thread_id = configurable.get("thread_id", "default")

    project_dir = Path.cwd()

    # sandbox: sandbox/workspace/{thread_id}/mockup_versions/v1/
    sandbox_path = SANDBOX / thread_id / "mockup_versions" / "v1"
    sandbox_path.mkdir(parents=True, exist_ok=True)

    # Lưu thêm 1 bản local trong project root (tiện hóa mockup/v1)
    mockup_dir = project_dir / "mockup"
    mockup_dir.mkdir(parents=True, exist_ok=True)
    html_dir = mockup_dir / "html"
    html_dir.mkdir(parents=True, exist_ok=True)
    version_dir = mockup_dir / "v1"
    version_dir.mkdir(parents=True, exist_ok=True)

    design = state.design_doc or ""
    prd = state.prd_v1 or state.prd_approved or ""
    requirements = state.prd_draft or ""

    # ── list screens from design (3 tầng fallback) ──
    screens = _list_screens(state)
    if not screens:
        print("  ⚠️ Không tìm thấy mục UI SCREENS trong design_doc, thử gọi LLM riêng để liệt kê lại...")
        screens = _list_screens_via_llm(state)
    if not screens:
        print("  ⚠️ LLM cũng không trả về danh sách hợp lệ, dùng bộ màn hình mặc định.")
        screens = [
            ("01_login", "Đăng nhập"),
            ("02_dashboard", "Trang chính"),
            ("03_detail", "Chi tiết"),
        ]
    print(f"  ✓ Sẽ generate {len(screens)} màn hình: {[s for s, _ in screens]}")

    # ── generate HTML + save to both sandbox & local ──
    html_paths: list[Path] = []
    llm_responses: list[LLMResponse] = []  # Lưu tất cả LLM responses để cộng dồn token
    
    for slug, label in screens:
        print(f"  → generating {slug} ({label})...")
        try:
            html = _generate_screen_html(slug, label, design, prd, requirements, 1, llm_responses)
            _save_html(html, html_dir, slug)
            path = _save_html(html, sandbox_path, slug)
            html_paths.append(path)
            print(f"  ✓ HTML saved: {path.name}")
        except Exception as e:
            print(f"  ⚠️ Screen '{slug}' failed, skipping: {e}")

    # ── capture PNG in sandbox ──
    png_paths: list[Path] = []
    try:
        png_paths = _capture_screens_to(html_paths, sandbox_path)
        print(f"  ✓ {len(png_paths)} screenshot PNG captured → {sandbox_path}")
    except Exception as e:
        print(f"  ⚠️ PNG capture failed: {e}")

    # ━━ return paths for frontend ━━
    mockup_screenshots: list[str] = [
        f"/artifacts/{thread_id}/mockup_versions/v1/{p.stem}.png"
        for p in png_paths
    ]

    # Gộp tất cả HTML thành nội dung mockup hoàn chỉnh
    all_html_content = "\n\n".join(
        f"<!-- Screen: {slug} -->" for slug, _ in screens
    ) + "\n\n" + "\n\n".join(
        path.read_text(encoding="utf-8") for path in html_paths if path.exists()
    )

    # --- Cập nhật node_stats ---
    node_name = "ui"
    gate_name = _NODE_GATES.get(node_name)
    total_tokens = sum(resp.total_tokens for resp in llm_responses)
    model = llm_responses[0].model if llm_responses else ""

    stats = dict(state.node_stats)
    existing = stats.get(node_name, {})
    stats[node_name] = {
        "reject_count": count_rejects(state.gate_history, gate_name) if gate_name else 0,
        "tokens_used": existing.get("tokens_used", 0) + total_tokens,
        "model": model,
    }

    # --- Cập nhật content_history ---
    all_history = dict(state.content_history)
    history = list(all_history.get(node_name, []))
    history.insert(0, {"content": all_html_content, "timestamp": datetime.now().isoformat()})
    history = history[:MAX_HISTORY_VERSIONS]
    all_history[node_name] = history

    return dict(
        mockup_screenshots=mockup_screenshots,
        _mockup_dir=str(mockup_dir),
        _version_dir=str(sandbox_path),
        node_stats=stats,
        content_history=all_history,
    )

# Alias để GraphBuilder dùng
UI_NODE = ui_node