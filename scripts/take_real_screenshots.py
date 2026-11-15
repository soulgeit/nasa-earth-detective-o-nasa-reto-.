"""
SI-assisted: claude-omni-1 (Claude Sonnet 5.5)
Script para capturar las 6 pantallas oficiales de la aplicación real (sin ?dev=fixture)
a 1600x900 en inglés contra el backend de FastAPI en vivo (http://127.0.0.1:8000).
Cumple con la Tarea 4 y la Regla 8 de docs/RONDA_2.md.
"""

import os
import time
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_DIR = os.path.join(BASE_DIR, "docs", "media")
os.makedirs(MEDIA_DIR, exist_ok=True)

URL = "http://127.0.0.1:8000/"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 900})
        page = context.new_page()

        print(f"1. Navigating to {URL}...")
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(2000)

        # Set English language
        page.evaluate("() => window.__etd.setLang('en')")
        page.wait_for_timeout(1000)

        # Capture 1: Main screen
        main_path = os.path.join(MEDIA_DIR, "main_screen.png")
        page.screenshot(path=main_path)
        print(f"Captured: {main_path}")

        # Capture 2: Real verdict for Lima T2M
        print("2. Investigating Lima T2M with real API...")
        page.evaluate("""() => {
            window.__etd.setMode('single');
            window.__etd.setPoint(-12.05, -77.03, 'Lima, Peru');
            const select = document.getElementById('variable-select');
            if (select) {
                select.value = 'T2M';
                window.__etd.onVariableChange?.();
            }
            document.getElementById('investigate-btn').click();
        }""")
        # Wait for real API response
        page.wait_for_timeout(5000)
        page.evaluate("() => document.getElementById('chart-heading').scrollIntoView({ behavior: 'instant', block: 'center' })")
        page.wait_for_timeout(1000)
        verdict_path = os.path.join(MEDIA_DIR, "verdict_view.png")
        page.screenshot(path=verdict_path)
        print(f"Captured: {verdict_path}")

        # Capture 3: Real TrendMap for Piura box
        print("3. Generating real TrendMap for Piura box...")
        page.evaluate("""() => {
            window.__etd.setMode('trendmap');
            window.__etd.setBBox([-82, -7, -78, -3]);
            document.getElementById('btn-calc-trendmap').click();
        }""")
        page.wait_for_timeout(5000)
        trendmap_path = os.path.join(MEDIA_DIR, "trendmap_spatial.png")
        page.evaluate("() => window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        page.screenshot(path=trendmap_path)
        print(f"Captured: {trendmap_path}")

        # Capture 4: Real Compare mode Lima vs Svalbard
        print("4. Comparing Lima vs Svalbard with real API...")
        page.evaluate("""() => {
            window.__etd.setMode('compare');
            window.__etd.setPointA(-12.05, -77.03, 'Lima, Peru');
            window.__etd.setPointB(78.22, 15.65, 'Arctic (Svalbard)');
            document.getElementById('investigate-btn').click();
        }""")
        page.wait_for_timeout(5000)
        compare_path = os.path.join(MEDIA_DIR, "compare_mode.png")
        page.evaluate("() => window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        page.screenshot(path=compare_path)
        print(f"Captured: {compare_path}")

        # Capture 5: AI Detective with plan and real explanation
        print("5. Asking the AI Detective...")
        page.evaluate("""() => {
            window.__etd.setMode('single');
            const input = document.getElementById('detective-input');
            if (input) {
                input.value = 'Is it raining less in Piura?';
                document.getElementById('detective-ask-btn').click();
            }
        }""")
        page.wait_for_timeout(4000)
        detective_path = os.path.join(MEDIA_DIR, "ai_detective_evidence.png")
        page.screenshot(path=detective_path)
        print(f"Captured: {detective_path}")

        # Capture 6: Not significant / high variability real case
        print("6. Investigating precipitation variability in Sechura Desert...")
        page.evaluate("""() => {
            window.__etd.setMode('single');
            window.__etd.setPoint(-5.55, -80.82, 'Sechura Desert, Peru');
            const select = document.getElementById('variable-select');
            if (select) {
                select.value = 'PRECTOTCORR';
            }
            document.getElementById('investigate-btn').click();
        }""")
        page.wait_for_timeout(5000)
        not_sig_path = os.path.join(MEDIA_DIR, "not_significant_case.png")
        page.evaluate("() => document.getElementById('chart-heading').scrollIntoView({ behavior: 'instant', block: 'center' })")
        page.wait_for_timeout(500)
        page.screenshot(path=not_sig_path)
        print(f"Captured: {not_sig_path}")

        browser.close()
        print("All 6 real screenshots successfully captured in docs/media/!")

if __name__ == "__main__":
    run()
