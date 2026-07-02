"""Standalone script: Render mockup HTML sang PNG bằng Playwright.

Chạy riêng biệt qua subprocess để tránh xung đột async event loop
với LangGraph runtime. Gọi: python scripts/render_mockup_png.py <html_path> <png_path>
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright


def main():
    if len(sys.argv) < 3:
        print("Usage: python render_mockup_png.py <html_path> <png_path>", file=sys.stderr)
        sys.exit(1)

    html_path = Path(sys.argv[1]).resolve()
    png_path = Path(sys.argv[2]).resolve()

    if not html_path.exists():
        print(f"[render] HTML file not found: {html_path}", file=sys.stderr)
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        try:
            page.goto(html_path.as_uri())
            page.wait_for_load_state("networkidle", timeout=30000)
            page.screenshot(path=str(png_path), full_page=True)
            print(f"[render] PNG saved: {png_path}")
        finally:
            page.close()
            browser.close()


if __name__ == "__main__":
    main()