"""
SI-assisted: claude-omni-1 (Claude Sonnet 5.5)
Render docs/demo/slides.html to docs/demo/EarthTrend_Detective_slides.pdf
Ensures exact 1280x720 16:9 dimensions, print background, and <= 7 pages.
"""

import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "docs" / "demo" / "slides.html"
PDF = ROOT / "docs" / "demo" / "EarthTrend_Detective_slides.pdf"

def main():
    if not HTML.exists():
        print(f"Error: {HTML} not found")
        sys.exit(1)

    file_url = HTML.as_uri()
    print(f"Loading {file_url}...")

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception:  # bundled Chromium not installed: use the system Chrome
            browser = p.chromium.launch(channel="chrome", headless=True)
        # Create page with exact 1280x720 viewport
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(file_url, wait_until="networkidle")
        page.wait_for_timeout(1500)

        # Count slide sections
        slide_count = page.evaluate("() => document.querySelectorAll('.slide').length")
        print(f"Found {slide_count} slides in HTML.")
        assert slide_count == 7, f"Expected 7 slides, found {slide_count}"

        # Generate PDF with exact dimensions
        page.pdf(
            path=str(PDF),
            width="1280px",
            height="720px",
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            page_ranges="1-7"
        )
        browser.close()

    if PDF.exists():
        size = PDF.stat().st_size
        print(f"SUCCESS: Generated {PDF} ({size} bytes).")
    else:
        print("FAILED: PDF not created.")
        sys.exit(1)

if __name__ == "__main__":
    main()
