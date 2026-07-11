"""
UINode: Generate HTML/CSS mockup screens trực tiếp (Giai đoạn 3.3) & render
preview PNG (Giai đoạn 3.4).

Từ Bước 1 (chuyển từ Puck sang GrapesJS): LLM sinh HTML/CSS tự do thay vì
UI JSON schema. HTML được lưu trực tiếp vào git (mockup/screens/*.html),
không cần bước trung gian render_screen_to_html(). PNG vẫn chụp qua Playwright
từ chính HTML LLM sinh ra.
"""

import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from langchain_core.runnables import RunnableConfig

from graph.state import (
    SoftwareFactoryState,
    count_rejects,
    update_node_stats,
    push_content_history,
)
from graph.repo_store import (
    save_mockup_screens,
    screenshot_dir,
    read_design_tokens,
    SANDBOX_ROOT,
)
from graph.schemas import DesignTokens
import json
from graph.json_utils import strip_code_fence

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
# HTML validation — lightweight parser check (thay Pydantic schema)
# ---------------------------------------------------------------------------

class _HTMLValidateParser(HTMLParser):
    """HTMLParser đơn giản để kiểm tra HTML có lỗi cơ bản không.

    Không nghiêm ngặt như validator W3C — chỉ bắt các lỗi rõ ràng:
    thẻ mở/đóng không khớp, thẻ tự đóng sai (vd <div/>), attribute
    thiếu giá trị. Đủ để phát hiện output LLM bị cắt ngang hoặc sai
    cú pháp nặng.
    """

    _VOID_ELEMENTS = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }

    def __init__(self):
        super().__init__()
        self.errors: list[str] = []
        self._open_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        tag_lower = tag.lower()
        # Bắt tag tự đóng sai cú pháp: <div/> thay vì <div> (HTML5 không cho phép)
        # HTMLParser không phân biệt, ta kiểm tra raw — nhưng ở đây chỉ log warning
        if tag_lower not in self._VOID_ELEMENTS:
            self._open_stack.append(tag_lower)

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if tag_lower in self._VOID_ELEMENTS:
            self.errors.append(f"Thẻ void element <{tag}> không nên có thẻ đóng </{tag}>")
            return
        if not self._open_stack:
            self.errors.append(f"Thẻ đóng </{tag}> không có thẻ mở tương ứng")
            return
        # Tìm thẻ mở khớp gần nhất (duyệt từ cuối stack)
        found = False
        for i in range(len(self._open_stack) - 1, -1, -1):
            if self._open_stack[i] == tag_lower:
                # Đóng tất cả thẻ con chưa đóng bên trong
                unclosed = self._open_stack[i + 1:]
                for uc in unclosed:
                    self.errors.append(f"Thẻ <{uc}> chưa được đóng trước khi đóng </{tag_lower}>")
                self._open_stack = self._open_stack[:i]
                found = True
                break
        if not found:
            self.errors.append(f"Thẻ đóng </{tag}> không khớp với thẻ mở nào trong stack")

    def handle_data(self, data: str):
        pass  # text content không cần validate

    def finalize(self):
        """Gọi sau khi parse xong — kiểm tra thẻ còn mở."""
        if self._open_stack:
            self.errors.append(
                f"Còn {len(self._open_stack)} thẻ chưa đóng: {', '.join(self._open_stack)}"
            )


def _validate_html(html: str) -> str | None:
    """Validate HTML cơ bản. Trả về None nếu OK, hoặc string mô tả lỗi."""
    if not html.strip():
        return "HTML rỗng — LLM không trả về nội dung"
    # Kiểm tra có ít nhất 1 thẻ HTML thực sự (không chỉ text thuần)
    if not re.search(r'<\s*(\w+)', html):
        return "Không tìm thấy thẻ HTML nào — output có thể là plain text, không phải HTML"
    parser = _HTMLValidateParser()
    try:
        parser.feed(html)
        parser.finalize()
    except Exception as e:
        return f"HTML parser crash: {e}"
    if parser.errors:
        # Giới hạn 5 lỗi đầu để không làm prompt retry quá dài
        return "HTML validation errors: " + "; ".join(parser.errors[:5])
    return None


# ---------------------------------------------------------------------------
# Phase 2 – generate one HTML per screen
# ---------------------------------------------------------------------------

def _generate_screen_html(
    screen_slug: str,
    screen_label: str,
    design: str,
    prd: str,
    tokens_json: str,
    previous_screens_summary: str,
):
    """Sinh HTML/CSS cho 1 màn hình — validate HTML cơ bản, retry 1 lần nếu sai.

    Trả về (html_content | None, llm_response, error_message | None).
    LLM trả về raw HTML (không code fence), ta strip fence + validate.
    """
    system_prompt = _read_prompt("ui_screen_html_system.txt")
    prd_summary = prd[:2000] if prd else ""

    user_msg_base = f"""THIẾT KẾ TỔNG THỂ:
{design[:3000] or 'Không có thiết kế chi tiết'}

YÊU CẦU CHỨC NĂNG:
{prd_summary}

DESIGN TOKENS (BẮT BUỘC dùng đúng màu/spacing/typography trong này):
{tokens_json}

CÁC MÀN HÌNH ĐÃ SINH TRƯỚC ĐÓ (để nhất quán style/class name):
{previous_screens_summary or '(chưa có màn hình nào trước đó)'}

SCREEN CẦN SINH: {screen_slug} | {screen_label}
"""

    last_error = ""
    for attempt in range(2):
        user_msg = user_msg_base
        if attempt > 0:
            user_msg += (
                f"\n\nLẦN TRƯỚC BẠN TRẢ VỀ HTML SAI, LỖI CỤ THỂ:\n{last_error}\n"
                "Hãy sửa lại và CHỈ trả về đúng 1 khối HTML hợp lệ (đầy đủ thẻ mở/đóng), không kèm gì khác."
            )
        prompt = f"{system_prompt}\n\n{user_msg}"
        llm_response = _ask_llm(prompt, max_tokens=8000, temperature=0.3)

        if llm_response.content is None:
            last_error = "LLM không trả về nội dung (network/API error)"
            continue

        cleaned = strip_code_fence(llm_response.content)
        html_err = _validate_html(cleaned)
        if html_err is not None:
            last_error = html_err
            continue

        return cleaned, llm_response, None

    return None, llm_response, last_error


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
    print("\n🚀 UINode: generating HTML/CSS mockup screens...")

    thread_id = "default"
    if config:
        configurable = config.get("configurable", {}) or {}
        thread_id = configurable.get("thread_id", "default")

    design = state.design_doc or ""
    prd = state.prd_v1 or state.prd_approved or ""

    # ── Giai đoạn 3.2/3.3: design_tokens BẮT BUỘC — không cho sinh screen
    # mới mà thiếu input này (đúng quyết định đã chốt trong kế hoạch) ──
    tokens_json = state.design_tokens or read_design_tokens(thread_id)
    if not tokens_json:
        print("  ✗ Không có design_tokens — dừng, không sinh mockup (chạy design_tokens_node trước).")
        return dict(
            mockup_screenshots=[],
            status="failed",
            error="Thiếu design_tokens — ui_node yêu cầu design_tokens_node phải chạy trước (Giai đoạn 3.1-3.2).",
        )
    try:
        tokens = DesignTokens.model_validate(json.loads(tokens_json))
    except Exception as e:
        print(f"  ✗ design_tokens hỏng, không parse được: {e}")
        return dict(
            mockup_screenshots=[],
            status="failed",
            error=f"design_tokens.json không hợp lệ: {e}",
        )

    # ── list screens from design (3 tầng fallback, giữ nguyên như cũ) ──
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

    # ── generate HTML/CSS từng màn hình — mỗi lần gọi kèm CONTEXT các màn
    # hình đã sinh trước đó trong CÙNG lần chạy này (nhất quán style/class
    # name giữa các màn) ──
    generated_files: list[dict] = []      # [{"filename": ..., "content": html_str}]
    generated_html_paths: list[Path] = []  # để chụp PNG ở bước sau
    previous_summary_lines: list[str] = []
    total_tokens = 0
    model_used = ""
    failed_screens: list[str] = []

    for slug, label in screens:
        print(f"  → generating {slug} ({label})...")
        previous_summary = "\n".join(previous_summary_lines) if previous_summary_lines else ""
        html_str, llm_response, error = _generate_screen_html(
            slug, label, design, prd, tokens_json, previous_summary
        )
        total_tokens += llm_response.total_tokens
        model_used = llm_response.model or model_used

        if html_str is None:
            print(f"  ⚠️ Screen '{slug}' thất bại sau retry: {error}")
            failed_screens.append(slug)
            continue

        generated_files.append({"filename": f"{slug}.html", "content": html_str})

        # Đoán các class CSS chính được dùng để tóm tắt cho context màn sau
        class_names = set(re.findall(r'class="([^"]+)"', html_str))
        tag_summary = ", ".join(sorted(class_names)[:6]) if class_names else "không rõ"
        previous_summary_lines.append(f"- {slug} ({label}): class chính [{tag_summary}]")

    # ── lưu HTML vào git repo project (1 commit/lần) ──
    html_paths: list[Path] = save_mockup_screens(thread_id, generated_files)
    if html_paths:
        print(f"  ✓ Đã lưu {len(html_paths)} file HTML vào git repo project ({thread_id})")

    # ── Giai đoạn 3.4: chụp PNG TRỰC TIẾP từ HTML LLM sinh (không cần
    # render_screen_to_html() trung gian nữa — HTML đã là HTML) ──
    shot_dir = screenshot_dir(thread_id)
    # Ghi HTML preview vào sandbox để Playwright đọc
    for entry in generated_files:
        slug = entry["filename"].replace(".html", "")
        preview_path = shot_dir / f"{slug}.preview.html"
        preview_path.write_text(entry["content"], encoding="utf-8")
        generated_html_paths.append(preview_path)

    png_paths: list[Path] = []
    if generated_html_paths:
        try:
            png_paths = _capture_screens_to(generated_html_paths, shot_dir)
            print(f"  ✓ {len(png_paths)} screenshot PNG captured → {shot_dir}")
        except Exception as e:
            print(f"  ⚠️ PNG capture failed: {e}")

    # ━━ URL cho frontend ━━
    # Lưu ý: frontend (App.tsx) tự thêm prefix "/artifacts/" khi render ảnh,
    # nên ở đây chỉ lưu đường dẫn tương đối từ WORKSPACE_ROOT, KHÔNG có /artifacts/
    # (không lặp lại prefix — tránh URL bị double /artifacts//artifacts/...)
    mockup_screenshots: list[str] = [
        p.relative_to(WORKSPACE_ROOT).as_posix()
        for p in png_paths
    ]

    # ── Observability: token/model/history ──
    node_stats = update_node_stats(
        state.node_stats, "ui",
        reject_count=count_rejects(state.gate_history, "gate_mockup"),
        tokens_used=total_tokens,
        model=model_used,
    )
    status_note = f" ({len(failed_screens)} lỗi: {failed_screens})" if failed_screens else ""
    screens_summary = f"{len(generated_files)}/{len(screens)} màn hình (HTML){status_note}: " + ", ".join(
        f["filename"].replace(".html", "") for f in generated_files
    )
    content_history = push_content_history(state.content_history, "ui", screens_summary)

    return dict(
        mockup_screenshots=mockup_screenshots,
        node_stats=node_stats,
        content_history=content_history,
    )

# Alias để GraphBuilder dùng
UI_NODE = ui_node
