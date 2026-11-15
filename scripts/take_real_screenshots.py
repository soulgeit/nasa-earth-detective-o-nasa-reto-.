"""
SI-assisted: claude-omni-1 (Claude Sonnet 5.5)
Script para capturar las 8 pantallas oficiales de la aplicación real (sin ?dev=fixture)
a 1600x900 en inglés contra el backend de FastAPI en vivo (http://127.0.0.1:8000),
más la captura oficial de móvil a 390px.
Cumple rigurosamente con docs/RONDA_5.md (§2.5 sin huecos en números, §3 Regla 29, §4 claude-omni-1).
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
        page.wait_for_timeout(1500)

        # Confirm English language (Rule 16)
        page.evaluate("() => window.__etd.setLang('en')")
        page.wait_for_timeout(1000)

        # Capture 1: Main screen (English, clean basemap and 15 variables)
        main_path = os.path.join(MEDIA_DIR, "main_screen.png")
        page.screenshot(path=main_path)
        print(f"Captured: {main_path}")

        # Capture 2: Real verdict for Lima T2M showing TESTS_DISAGREE breakdown & Sen fan
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
        page.wait_for_selector("#result-root:not([hidden])", timeout=15000)
        page.wait_for_timeout(1000)
        page.evaluate("() => window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        verdict_path = os.path.join(MEDIA_DIR, "verdict_view.png")
        page.screenshot(path=verdict_path)
        print(f"Captured: {verdict_path}")

        # Capture 3: Real TrendMap / Atlas Global
        print("3. Generating real Atlas / TrendMap...")
        page.evaluate("""() => {
            window.__etd.setMode('trendmap');
            document.getElementById('btn-load-atlas').click();
        }""")
        page.wait_for_selector("#trendmap-root:not([hidden])", timeout=15000)
        page.wait_for_timeout(1000)
        page.evaluate("() => window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        trendmap_path = os.path.join(MEDIA_DIR, "trendmap_spatial.png")
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
        page.wait_for_selector("#compare-root:not([hidden])", timeout=15000)
        page.wait_for_timeout(1000)
        page.evaluate("() => window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        compare_path = os.path.join(MEDIA_DIR, "compare_mode.png")
        page.screenshot(path=compare_path)
        print(f"Captured: {compare_path}")

        # Capture 5: AI Detective with plan confirmed and real extractive citations
        print("5. Asking the AI Detective and confirming investigation...")
        page.evaluate("""() => {
            window.__etd.setMode('single');
            const input = document.getElementById('detective-input');
            if (input) {
                input.value = 'How is air temperature changing in Lima?';
                document.getElementById('detective-ask-btn').click();
            }
        }""")
        page.wait_for_selector('#detective-plan-card:not([hidden])', timeout=5000)
        page.wait_for_timeout(500)

        # Capture 5B: Plan attribution badge ("Planned by: rules / LoRA")
        plan_attr_path = os.path.join(MEDIA_DIR, "plan_attribution.png")
        page.screenshot(path=plan_attr_path)
        print(f"Captured: {plan_attr_path}")

        # Click Confirm & Investigate
        page.evaluate("""() => document.getElementById('plan-confirm-btn').click()""")
        page.wait_for_selector('#result-root:not([hidden])', timeout=15000)
        page.wait_for_timeout(2500)
        page.evaluate("""() => document.getElementById('explain-plate').scrollIntoView({ behavior: 'instant', block: 'start' })""")
        page.wait_for_timeout(500)
        detective_path = os.path.join(MEDIA_DIR, "ai_detective_evidence.png")
        page.screenshot(path=detective_path)
        print(f"Captured: {detective_path}")

        # Capture 6: Cases Gallery (7 official frozen cases)
        print("6. Capturing frozen cases gallery...")
        page.evaluate("() => window.__etd.setMode('cases')")
        page.wait_for_timeout(1000)
        gallery_path = os.path.join(MEDIA_DIR, "cases_gallery.png")
        page.screenshot(path=gallery_path)
        print(f"Captured: {gallery_path}")

        # Capture 7: Not significant case (Antarctic sea ice - honest scientific verdict)
        print("7. Investigating Antarctic Sea Ice (Not Significant case)...")
        page.evaluate("""() => {
            window.__etd.setMode('single');
            const c = window.__etd.state.cases.find(x => x.id === 'antarctic-seaice');
            if (c) window.__etd.openCase(c);
        }""")
        page.wait_for_selector("#result-root:not([hidden])", timeout=15000)
        page.wait_for_timeout(1000)
        page.evaluate("() => window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        not_sig_path = os.path.join(MEDIA_DIR, "not_significant_case.png")
        page.screenshot(path=not_sig_path)
        print(f"Captured: {not_sig_path}")

        context.close()

        # Capture 8: Mobile 390px overview
        print("8. Capturing mobile 390px viewport...")
        m_ctx = browser.new_context(viewport={"width": 390, "height": 844})
        m_page = m_ctx.new_page()
        m_page.goto(URL, wait_until="networkidle")
        m_page.evaluate("() => window.__etd.setLang('en')")
        m_page.wait_for_timeout(1000)
        m_page.evaluate("""() => {
            window.__etd.setPoint(-12.05, -77.03, 'Lima, Peru');
            document.getElementById('investigate-btn').click();
        }""")
        m_page.wait_for_selector("#result-root:not([hidden])", timeout=15000)
        m_page.wait_for_timeout(1000)
        mobile_path = os.path.join(MEDIA_DIR, "mobile_390_overview.png")
        m_page.screenshot(path=mobile_path)
        print(f"Captured: {mobile_path}")
        m_ctx.close()

        browser.close()
        print("All 8 official screenshots + mobile successfully updated in docs/media/!")

if __name__ == "__main__":
    run()
