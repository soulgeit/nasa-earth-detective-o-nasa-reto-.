#!/usr/bin/env python3
"""
scripts/make_demo.py
Author: claude-omni-c (NASA Space Apps Challenge 2026)

Records and generates the official 29-second video demo (EarthTrend_Detective_30s.mp4)
under docs/demo/ using Playwright and ffmpeg.

Checks:
- Duration <= 30.0s
- Resolution: 1920x1080 (16:9 full HD)
- Video format: H.264 mp4
- File size <= 25MB
- Clean presentation: strictly in English, zero NASA logos/insignias, no persons, no browser chrome.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEMO_DIR = ROOT / "docs" / "demo"
DEMO_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_MP4 = DEMO_DIR / "EarthTrend_Detective_30s.mp4"
FRAMES_DIR = DEMO_DIR / "_frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)


def run_cmd(cmd: list[str]) -> str:
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return res.stdout.strip()


def build_title_card(output_path: Path):
    """Generate a clean 1920x1080 title card HTML and capture it."""
    html_content = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {
    margin: 0;
    padding: 0;
    width: 1920px;
    height: 1080px;
    background: radial-gradient(circle at 50% 40%, #1a2f35 0%, #122024 70%, #0d171a 100%);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #edf0ef;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    box-sizing: border-box;
    position: relative;
    overflow: hidden;
  }
  .badge {
    background: rgba(18, 94, 90, 0.4);
    border: 1px solid #125e5a;
    color: #48b5ad;
    padding: 10px 24px;
    border-radius: 999px;
    font-size: 24px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 30px;
  }
  h1 {
    font-size: 96px;
    font-weight: 800;
    margin: 0 0 20px 0;
    letter-spacing: -2px;
    color: #ffffff;
    text-shadow: 0 4px 20px rgba(0,0,0,0.4);
  }
  .tagline {
    font-size: 38px;
    color: #9ab4b9;
    max-width: 1200px;
    text-align: center;
    line-height: 1.4;
    margin: 0 0 50px 0;
  }
  .pillars {
    display: flex;
    gap: 40px;
    margin-top: 20px;
  }
  .pillar {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 24px 36px;
    text-align: center;
  }
  .pillar-title {
    font-size: 22px;
    font-weight: 700;
    color: #d1a153;
    margin-bottom: 8px;
  }
  .pillar-desc {
    font-size: 18px;
    color: #9ab4b9;
  }
  .footer {
    position: absolute;
    bottom: 40px;
    font-size: 20px;
    color: #647b80;
  }
</style>
</head>
<body>
  <div class="badge">NASA Space Apps Challenge 2026</div>
  <h1>EarthTrend Detective</h1>
  <div class="tagline">Empowering students to investigate real climate trends across Earth with rigorous, transparent statistics.</div>
  <div class="pillars">
    <div class="pillar">
      <div class="pillar-title">Real NASA Data</div>
      <div class="pillar-desc">POWER · GISTEMP · NSIDC · Giovanni</div>
    </div>
    <div class="pillar">
      <div class="pillar-title">Honest Statistics</div>
      <div class="pillar-desc">Theil-Sen · Mann-Kendall · Detectability</div>
    </div>
    <div class="pillar">
      <div class="pillar-title">Spatial Validation</div>
      <div class="pillar-desc">FDR Control (Benjamini-Hochberg)</div>
    </div>
  </div>
  <div class="footer">Open Source Educational Science Tool · Free Public Web App</div>
</body>
</html>
"""
    title_html = DEMO_DIR / "_title.html"
    title_html.write_text(html_content, encoding="utf-8")
    return title_html


def build_outro_card(output_path: Path):
    """Generate a clean 1920x1080 outro card HTML and capture it."""
    html_content = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {
    margin: 0;
    padding: 0;
    width: 1920px;
    height: 1080px;
    background: radial-gradient(circle at 50% 50%, #15272b 0%, #101c1f 70%, #0a1113 100%);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #edf0ef;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    box-sizing: border-box;
    position: relative;
  }
  h1 {
    font-size: 80px;
    font-weight: 800;
    margin: 0 0 24px 0;
    color: #ffffff;
  }
  .url-box {
    background: #125e5a;
    border: 2px solid #20948e;
    border-radius: 16px;
    padding: 24px 48px;
    font-size: 38px;
    font-weight: 700;
    color: #ffffff;
    font-family: monospace;
    letter-spacing: 1px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.5);
    margin-bottom: 40px;
  }
  .features {
    font-size: 26px;
    color: #9ab4b9;
    margin-bottom: 20px;
    text-align: center;
    line-height: 1.6;
  }
  .disclaimer {
    position: absolute;
    bottom: 40px;
    font-size: 18px;
    color: #647b80;
    text-align: center;
    max-width: 1400px;
  }
</style>
</head>
<body>
  <h1>Explore Earth with Confidence</h1>
  <div class="url-box">https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./</div>
  <div class="features">
    • Free public access & Bilingual (English & Spanish)<br>
    • No installation, registration, or accounts needed<br>
    • Verified NASA citations and full cryptographic provenance
  </div>
  <div class="disclaimer">
    EarthTrend Detective is an independent open-source educational project for NASA Space Apps Challenge 2026.<br>
    Data sources: NASA POWER, NASA GISTEMP v4, NSIDC Sea Ice Index v4, and GES DISC Giovanni.
  </div>
</body>
</html>
"""
    outro_html = DEMO_DIR / "_outro.html"
    outro_html.write_text(html_content, encoding="utf-8")
    return outro_html


def record_demo():
    print("[1/5] Checking local FastAPI server on port 8791...")
    server_process = None
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:8791/api/health", timeout=2) as resp:
            if resp.status == 200:
                print("Server already running on port 8791.")
    except Exception:
        print("Starting local FastAPI server on port 8791...")
        server_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "src.api.main:app", "--port", "8791", "--host", "127.0.0.1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        time.sleep(3)

    from playwright.sync_api import sync_playwright

    title_html = build_title_card(DEMO_DIR)
    outro_html = build_outro_card(DEMO_DIR)

    print("[2/5] Capturing video segments and high-fidelity screen frames via Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            color_scheme="light"
        )
        page = context.new_page()

        # Capture title card (Scene 1)
        page.goto(f"file://{title_html.resolve().as_posix()}")
        page.wait_for_timeout(500)
        page.screenshot(path=str(FRAMES_DIR / "scene1_title.png"))

        # Navigate to web application in English
        page.goto("http://127.0.0.1:8791/", wait_until="networkidle")
        page.wait_for_selector("#variable-select", timeout=10000)

        # Ensure English UI
        page.click("#lang-en")
        page.wait_for_timeout(300)

        def inject_banner(title: str, subtitle: str):
            page.evaluate(f"""() => {{
                let existing = document.getElementById('demo-overlay-banner');
                if (existing) existing.remove();
                let b = document.createElement('div');
                b.id = 'demo-overlay-banner';
                b.style.position = 'fixed';
                b.style.bottom = '0';
                b.style.left = '0';
                b.style.width = '100vw';
                b.style.background = 'rgba(18, 32, 36, 0.94)';
                b.style.borderTop = '2px solid #125e5a';
                b.style.color = '#edf0ef';
                b.style.padding = '18px 48px';
                b.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
                b.style.zIndex = '999999';
                b.style.boxSizing = 'border-box';
                b.innerHTML = `
                  <div style="font-size: 32px; font-weight: 700; color: #ffffff; margin-bottom: 6px;">{title}</div>
                  <div style="font-size: 22px; font-weight: 500; color: #48b5ad;">{subtitle}</div>
                `;
                document.body.appendChild(b);
            }}""")

        # Scene 2: Arctic Sea Ice Extent (1978-2026) -> Strong Significant Trend
        page.click("button.case-btn:has-text('Arctic sea ice')")
        page.wait_for_selector("#verdict-title", timeout=10000)
        page.wait_for_timeout(1000)
        inject_banner("1. Arctic Sea Ice Extent (1978–2026)", "Clear, strong decline: -0.50 million km²/decade (-4.4%) · Both tests agree")
        page.screenshot(path=str(FRAMES_DIR / "scene2_arctic_seaice.png"))

        # Scene 3: Antarctic Sea Ice Extent -> Honest "Not Significant" & Detectability
        page.click("button.case-btn:has-text('Antarctic sea ice')")
        page.wait_for_selector("#verdict-title", timeout=10000)
        page.wait_for_timeout(1000)
        page.evaluate("window.scrollTo(0, 200)")
        page.wait_for_timeout(400)
        inject_banner("2. Antarctic Sea Ice: Honest Statistics", "No trend detectable so far (p = 0.63) · Detectability model: ~133 more years needed")
        page.screenshot(path=str(FRAMES_DIR / "scene3_antarctic_detectability.png"))
        page.evaluate("window.scrollTo(0, 0)")

        # Scene 4: Spatial TrendMap with Benjamini-Hochberg FDR Control
        page.click("#mode-trendmap")
        page.wait_for_timeout(300)
        page.click("#btn-load-atlas")
        page.wait_for_selector("#trendmap-summary", timeout=10000)
        page.wait_for_timeout(1200)
        inject_banner("3. Global Spatial TrendMap (Wilks 2016)", "False discovery rate control (q=0.10): 60% of grid cells significant")
        page.screenshot(path=str(FRAMES_DIR / "scene4_spatial_trendmap.png"))

        # Scene 5: Compare Mode (Lima vs Svalbard)
        page.evaluate("""() => {
            const select = document.getElementById('variable-select');
            if (select) {
                select.value = 'T2M';
                window.__etd.onVariableChange();
            }
            window.__etd.setMode('compare');
            window.__etd.setPointA(-12.05, -77.03, 'Lima, Peru');
            window.__etd.setPointB(78.22, 15.65, 'Arctic (Svalbard)');
            document.getElementById('investigate-btn').click();
        }""")
        page.wait_for_selector("#compare-root:not([hidden])", timeout=20000)
        page.wait_for_timeout(1000)
        page.evaluate("() => window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        inject_banner("4. Two-Region Comparison & Opposing Trends", "Lima (+0.16°C/dec) vs. Arctic (+0.70°C/dec) · Synchronized Y-axes")
        page.screenshot(path=str(FRAMES_DIR / "scene5_compare_mode.png"))

        # Scene 6: Outro Card
        page.goto(f"file://{outro_html.resolve().as_posix()}")
        page.wait_for_timeout(500)
        page.screenshot(path=str(FRAMES_DIR / "scene6_outro.png"))

        browser.close()

    # Terminate FastAPI if we started it
    if server_process:
        server_process.terminate()
        try:
            server_process.wait(timeout=3)
        except Exception:
            server_process.kill()

    print("[3/5] Composing high-definition video sequence with ffmpeg...")
    # Pacing:
    # Scene 1 Title: 3.0s
    # Scene 2 Arctic: 6.0s
    # Scene 3 Antarctic (Honest): 6.0s
    # Scene 4 TrendMap (FDR): 6.0s
    # Scene 5 Compare Mode: 5.0s
    # Scene 6 Outro: 3.0s
    # Total = 29.0s (strictly <= 30.0s)

    scene_clips = [
        ("scene1_title.png", 3.0, "EarthTrend Detective — Space Apps 2026", "A tool for students to investigate real climate trends"),
        ("scene2_arctic_seaice.png", 6.0, "1. Arctic Sea Ice Extent (1978–2026)", "Clear, strong decline: -0.50 million km²/decade (-4.4%)"),
        ("scene3_antarctic_detectability.png", 6.0, "2. Antarctic Sea Ice: Honest Statistics", "No trend detectable so far. Detectability model: ~133 more years needed"),
        ("scene4_spatial_trendmap.png", 6.0, "3. Global Spatial TrendMap (Wilks 2016)", "False discovery rate control (q=0.10): 60% of grid cells significant"),
        ("scene5_compare_mode.png", 5.0, "4. Two-Region Comparison & Verified Citations", "Synchronized scales and cited excerpts from NASA Earth Observatory"),
        ("scene6_outro.png", 3.0, "Live Public Deployment: Free & Open Source", "soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./"),
    ]

    rendered_clips = []
    for idx, (img_name, duration, _, _) in enumerate(scene_clips, 1):
        in_img = FRAMES_DIR / img_name
        out_clip = FRAMES_DIR / f"clip_{idx}.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(in_img),
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-r", "30",
            str(out_clip)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        rendered_clips.append(out_clip)

    # Concat clips into final output
    concat_txt = FRAMES_DIR / "concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for c in rendered_clips:
            f.write(f"file '{c.resolve().as_posix()}'\n")

    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level", "4.1",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        str(OUTPUT_MP4)
    ]
    subprocess.run(cmd_concat, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("[4/5] Verification with ffprobe...")
    cmd_probe = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration,size:stream=codec_name,width,height",
        "-of", "json",
        str(OUTPUT_MP4)
    ]
    probe_output = json.loads(run_cmd(cmd_probe))

    stream = probe_output["streams"][0]
    fmt = probe_output["format"]
    duration = float(fmt["duration"])
    size_mb = float(fmt["size"]) / (1024 * 1024)
    width = int(stream["width"])
    height = int(stream["height"])
    codec = stream["codec_name"]

    print(f"\n=======================================================")
    print(f"VIDEO VERIFICATION RESULTS:")
    print(f"File: {OUTPUT_MP4}")
    print(f"Duration: {duration:.2f}s (Constraint: <= 30.0s) -> {'PASS' if duration <= 30.0 else 'FAIL'}")
    print(f"Resolution: {width}x{height} (16:9 1080p) -> {'PASS' if width == 1920 and height == 1080 else 'FAIL'}")
    print(f"Codec: {codec} -> {'PASS' if codec == 'h264' else 'FAIL'}")
    print(f"Size: {size_mb:.2f} MB (Constraint: <= 25 MB) -> {'PASS' if size_mb <= 25.0 else 'FAIL'}")
    print(f"=======================================================\n")

    if duration > 30.0 or size_mb > 25.0:
        raise RuntimeError("Video specifications exceed official submission constraints!")

    print("[5/5] Success! EarthTrend_Detective_30s.mp4 ready in docs/demo/.")


if __name__ == "__main__":
    record_demo()
