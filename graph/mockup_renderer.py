"""Render mockup HTML sang PNG bằng Playwright.

Gọi script riêng biệt qua subprocess để tránh xung đột async event loop
với LangGraph runtime. Mỗi lần render mở/đóng Chromium riêng — đơn giản,
an toàn, không cần quản lý lifecycle.
"""

import subprocess
import sys
from pathlib import Path

# Path đến script render standalone (static full-page render)
_RENDER_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "render_mockup_png.py"


def render_html_to_png(html_path: Path, png_path: Path) -> None:
    """Render file HTML sang ảnh PNG qua subprocess.

    Args:
        html_path: Đường dẫn file .html
        png_path: Đường dẫn file .png đầu ra

    Raises:
        RuntimeError: Nếu subprocess trả về mã lỗi
    """
    result = subprocess.run(
        [sys.executable, str(_RENDER_SCRIPT), str(html_path), str(png_path)],
        capture_output=True,
        text=True,
        timeout=60,  # timeout 60s cho trường hợp Tailwind CDN tải chậm
    )

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(f"Playwright render failed (exit {result.returncode}): {stderr}")

    if not png_path.exists():
        raise RuntimeError(f"PNG file not created: {png_path}")


def render_screens_to_png(html_paths: list[Path]) -> list[Path]:
    """Render từng file HTML sang PNG cùng thư mục.
    
    Args:
        html_paths: list Path của các file HTML cần render
    
    Returns:
        list Path PNG đã tạo (bỏ qua file nào lỗi).
    """
    results: list[Path] = []
    for html_path in html_paths:
        png_path = html_path.with_suffix(".png")
        try:
            render_html_to_png(html_path, png_path)
            results.append(png_path)
        except Exception as e:
            print(f"[mockup_renderer] lỗi render {html_path.name}: {e}")
    return results


def capture_screens(html_paths: list[Path]) -> list[Path]:
    """Mỗi file HTML = 1 màn hình, chụp 1 ảnh, không click gì cả.
    
    Gọi ``capture_mockup.py`` qua subprocess. Script dùng Playwright 
    mở từng file HTML và chụp full-page screenshot.
    
    Args:
        html_paths: list Path các file HTML cần capture
    
    Returns:
        list Path ảnh PNG đã tạo.
    """
    if not html_paths:
        return []

    # Chụp vào cùng thư mục với file HTML
    output_dir = html_paths[0].parent
    paths_str = [str(p.resolve()) for p in html_paths]

    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / "tools" / "capture_mockup.py"),
         str(output_dir)] + paths_str,
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode != 0:
        print(f"[mockup_renderer] capture subprocess failed (exit {result.returncode}): {result.stderr}")
        # Fallback: static render từng file
        return render_screens_to_png(html_paths)

    # Parse stdout lấy PNG paths
    screenshots = []
    for line in result.stdout.splitlines():
        if "[capture]" in line and "->" in line:
            parts = line.split("->")
            if len(parts) == 2:
                png = parts[1].strip()
                if Path(png).exists():
                    screenshots.append(Path(png))

    if not screenshots:
        print("[mockup_renderer] không parse được path PNG nào, fallback static render")
        return render_screens_to_png(html_paths)

    return screenshots