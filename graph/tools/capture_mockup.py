"""Capture mỗi file HTML thành 1 PNG — không detect tab, không click gì cả."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright


def capture_screens(html_paths: list[str], output_dir: str) -> list[str]:
    """Mỗi file HTML = 1 màn hình, chụp 1 ảnh, không click gì cả."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        for html_path in html_paths:
            png_path = out / (Path(html_path).stem + ".png")
            page.goto(Path(html_path).resolve().as_uri())
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1000)  # chờ Tailwind render
            page.screenshot(path=str(png_path), full_page=True)
            results.append(str(png_path))
            print(f"[capture] {html_path} -> {png_path}")

        browser.close()

    return results


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python capture_mockup.py <output_dir> <html_path1> [html_path2 ...]")
        sys.exit(1)
    output_dir = sys.argv[1]
    html_paths = sys.argv[2:]
    capture_screens(html_paths, output_dir)