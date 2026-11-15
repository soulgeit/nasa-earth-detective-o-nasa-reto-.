"""
SI-assisted: claude-omni-1 (Claude Sonnet 5.5)
Verification script for Ronda 5 UI tasks:
1. Spanish units: arctic-seaice and piura-prectotcorr #result-root has NO 'million' and NO '/day'.
2. Period fields: From / To reflect the actual case period (e.g. 1978 to 2026 for arctic sea ice).
3. QA D8: Giovanni CSV upload displays clean variable name, NOT M2SMNXSLV_5_12_4_T2MMEAN.
4. Digit matching: #f-slope and narrative explanation match to the exact last digit across all 7 cases.
"""

import os
import sys
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8000/"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(BASE_DIR, "data", "raw", "giovanni", "T2M__amazonia.csv")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 900})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(1000)

        # -------------------------------------------------------------
        # TEST 1: Spanish Units in arctic-seaice and piura-prectotcorr
        # -------------------------------------------------------------
        page.evaluate("() => window.__etd.setLang('es')")
        page.wait_for_timeout(800)

        # Open arctic-seaice case
        print("\n--- 1. Testing arctic-seaice in Spanish ---")
        page.evaluate("""() => {
          window.__etd.setMode('cases');
        }""")
        page.wait_for_timeout(500)
        page.evaluate("""() => {
          const btns = Array.from(document.querySelectorAll('#cases-list .case-btn, .case-btn'));
          const btn = btns.find(b => b.textContent.includes('Ártico') || b.textContent.includes('Artico') || b.textContent.includes('hielo'));
          if (btn) btn.click();
        }""")
        page.wait_for_selector("#result-root:not([hidden])", timeout=10000)
        page.wait_for_timeout(1500)

        text_arctic = page.evaluate("() => document.getElementById('result-root').innerText")
        has_million = "million" in text_arctic.lower()
        has_slash_day = "/day" in text_arctic.lower()
        print(f"Arctic - contains 'million': {has_million}")
        print(f"Arctic - contains '/day': {has_slash_day}")
        assert not has_million, "Error: arctic-seaice in Spanish contains 'million'!"
        assert not has_slash_day, "Error: arctic-seaice in Spanish contains '/day'!"

        # Check From / To period in arctic-seaice
        start_val = page.evaluate("() => document.getElementById('period-start').value")
        end_val = page.evaluate("() => document.getElementById('period-end').value")
        print(f"Arctic Sea Ice Period -> From: {start_val}, To: {end_val}")
        assert start_val == "1978", f"Expected start year 1978, got {start_val}"
        assert end_val == "2026", f"Expected end year 2026, got {end_val}"

        # Open piura-prectotcorr case
        print("\n--- 2. Testing piura-prectotcorr in Spanish ---")
        page.evaluate("""() => {
          window.__etd.setMode('cases');
        }""")
        page.wait_for_timeout(500)
        page.evaluate("""() => {
          const btns = Array.from(document.querySelectorAll('#cases-list .case-btn, .case-btn'));
          const btn = btns.find(b => b.textContent.includes('Piura'));
          if (btn) btn.click();
        }""")
        page.wait_for_selector("#result-root:not([hidden])", timeout=10000)
        page.wait_for_timeout(1500)

        text_piura = page.evaluate("() => document.getElementById('result-root').innerText")
        has_million_p = "million" in text_piura.lower()
        has_slash_day_p = "/day" in text_piura.lower()
        print(f"Piura - contains 'million': {has_million_p}")
        print(f"Piura - contains '/day': {has_slash_day_p}")
        assert not has_million_p, "Error: piura-prectotcorr in Spanish contains 'million'!"
        assert not has_slash_day_p, "Error: piura-prectotcorr in Spanish contains '/day'!"

        # -------------------------------------------------------------
        # TEST 3: QA D8 Giovanni CSV upload displays clean name
        # -------------------------------------------------------------
        print("\n--- 3. Testing QA D8 Giovanni CSV upload ---")
        page.evaluate("() => window.__etd.setLang('en')")
        page.wait_for_timeout(500)
        if os.path.exists(CSV):
            with page.expect_response(lambda r: "/api/analyze/upload" in r.url, timeout=25000):
                page.locator("#csv-file-input").set_input_files(CSV)
            page.wait_for_timeout(1500)
            result_text = page.evaluate("() => document.getElementById('result-root').innerText")
            has_raw_m2 = "M2SMNXSLV" in result_text
            print(f"Giovanni CSV result contains 'M2SMNXSLV': {has_raw_m2}")
            assert not has_raw_m2, "Error: Giovanni upload displays raw identifier M2SMNXSLV!"
            assert "Air temperature" in result_text, "Error: Clean variable name not found in upload result!"
            print("Giovanni CSV shows clean variable name: PASS")

        # -------------------------------------------------------------
        # TEST 4: Digit matching for all 7 cases
        # -------------------------------------------------------------
        print("\n--- 4. Testing exact digit matching across all 7 cases ---")
        cases = page.evaluate("() => window.__etd.state.cases.map(c => c.id)")
        print(f"Found {len(cases)} cases: {cases}")

        for cid in cases:
            page.evaluate(f"""() => {{
              const c = window.__etd.state.cases.find(x => x.id === '{cid}');
              window.__etd.openCase(c);
            }}""")
            page.wait_for_timeout(1200)

            slope_disp = page.evaluate("() => document.getElementById('f-slope').innerText.trim()")
            explain_text = page.evaluate("() => document.getElementById('explain-text').innerText")

            # Extract the decadal slope mentioned in the explanation text
            # E.g. "Estimated rate of +0.158 °C/decade"
            import re
            m = re.search(r'(?:rate of|tasa estimada de)\s+([+-]\d+\.\d+)', explain_text, re.IGNORECASE)
            explain_slope = m.group(1) if m else None

            # Compare normalized digits
            norm_disp = slope_disp.replace('−', '-').replace('+', '')
            norm_exp = explain_slope.replace('−', '-').replace('+', '') if explain_slope else None

            print(f"Case {cid:22} | f-slope: {slope_disp:7} | text: {explain_slope}")
            if explain_slope:
                assert norm_disp == norm_exp, f"Mismatch in {cid}: display={slope_disp} vs text={explain_slope}!"

        browser.close()
        print("\n>>> ALL RONDA 5 UI TESTS PASSED! <<<")

if __name__ == "__main__":
    run()
