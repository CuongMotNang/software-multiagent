"""
UINode: Generate HTML mockup screens & render to PNG.
"""

import re
from pathlib import Path
from typing import Any

from langchain_core.runnables import RunnableConfig

from graph.state import (
    SoftwareFactoryState,
    count_rejects,
    update_node_stats,
    push_content_history,
)
from graph.artifact_store import save_mockup_screens, SANDBOX_ROOT

CUR_DIR = Path(__file__).parent.parent.resolve()
PROMPT_DIR = CUR_DIR / ".." / "prompts"
# Dùng chung SANDBOX_ROOT với artifact_store.py (KHÔNG tự tính tay riêng)
# để tránh lệch cấu trúc thư mục — artifact_store lưu vào
# sandbox/workspace/{thread_id}/artifacts/..., không phải
# sandbox/workspace/{thread_id}/... như code cũ từng hardcode.
WORKSPACE_ROOT = SANDBOX_ROOT / "workspace"

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


def _ask_llm(prompt: str, *, max_tokens=20000, **kwargs):
    """Trả về LLMResponse đầy đủ (content + usage + model), KHÔNG chỉ string,
    để ui_node() cộng dồn được token qua nhiều lần gọi (mỗi màn hình 1 lần).
    """
    import os
    from graph.llm import llm_factory

    provider_name = os.getenv("UI_PROVIDER", None)
    llm = llm_factory(provider_name)
    return llm.call(
        system_prompt="",
        user_prompt=prompt,
        temperature=kwargs.get("temperature", 0.3),
        max_tokens=max_tokens,
    )


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

    Lưu ý: token của lệnh gọi này KHÔNG được cộng vào node_stats["ui"]
    (đơn giản hoá phạm vi) — chỉ token của các lệnh gọi generate HTML mới
    được tính, vì đó là phần chiếm phần lớn chi phí thực tế.
    """
    system_prompt = _read_prompt("ui_screens_list.txt")
    if not system_prompt:
        return []

    design = state.design_doc or ""
    prompt = f"{system_prompt}\n\n## TÀI LIỆU THIẾT KẾ\n\n{design[:6000]}"
    llm_response = _ask_llm(prompt, max_tokens=1024)
    raw = llm_response.content or ""

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
                            version: int):
    """Trả về tuple (html, llm_response) — llm_response dùng để ui_node()
    cộng dồn token/model qua nhiều lần gọi (1 lần / màn hình).
    """
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
    html = _extract_single_html(llm_response.content or "")
    return html, llm_response

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

    # ── generate HTML (giữ trong bộ nhớ, chưa ghi file vội) ──
    generated: list[dict] = []  # [{"filename": ..., "html": ...}]
    total_tokens = 0
    model_used = ""
    for slug, label in screens:
        print(f"  → generating {slug} ({label})...")
        try:
            html, llm_response = _generate_screen_html(slug, label, design, prd, requirements, 1)
            total_tokens += llm_response.total_tokens
            model_used = llm_response.model or model_used
            generated.append({"filename": f"{slug}.html", "html": html})
        except Exception as e:
            print(f"  ⚠️ Screen '{slug}' failed, skipping: {e}")

    # ── lưu vào đúng version mới (tự tăng v1, v2, v3... — KHÔNG hardcode v1
    # và KHÔNG ghi đè bản cũ như code trước đây) ──
    html_paths: list[Path] = save_mockup_screens(thread_id, generated)
    version_dir = html_paths[0].parent if html_paths else None
    if version_dir:
        print(f"  ✓ Đã lưu {len(html_paths)} file HTML vào {version_dir}")

    # ── capture PNG cùng thư mục version vừa lưu ──
    png_paths: list[Path] = []
    if version_dir:
        try:
            png_paths = _capture_screens_to(html_paths, version_dir)
            print(f"  ✓ {len(png_paths)} screenshot PNG captured → {version_dir}")
        except Exception as e:
            print(f"  ⚠️ PNG capture failed: {e}")

    # ━━ URL cho frontend: tính từ path thật, không hardcode cấu trúc thư mục,
    # để không lệch nếu artifact_store.py đổi cấu trúc lưu trữ sau này. ━━
    mockup_screenshots: list[str] = [
        f"/artifacts/{p.relative_to(WORKSPACE_ROOT).as_posix()}"
        for p in png_paths
    ]

    # ── Observability: token/model/history ──
    # gate_mockup đứng ngay sau "ui" trong graph (ui -> gate_mockup).
    # content_history của "ui" lưu 1 bản tóm tắt (danh sách slug + version)
    # thay vì toàn bộ HTML nhiều màn hình (tránh phình quá to mỗi lần lưu).
    node_stats = update_node_stats(
        state.node_stats, "ui",
        reject_count=count_rejects(state.gate_history, "gate_mockup"),
        tokens_used=total_tokens,
        model=model_used,
    )
    version_label = version_dir.name if version_dir else "?"
    screens_summary = f"[{version_label}] {len(screens)} màn hình: " + ", ".join(s for s, _ in screens)
    content_history = push_content_history(state.content_history, "ui", screens_summary)

    return dict(
        mockup_screenshots=mockup_screenshots,
        node_stats=node_stats,
        content_history=content_history,
    )

# Alias để GraphBuilder dùng
UI_NODE = ui_node