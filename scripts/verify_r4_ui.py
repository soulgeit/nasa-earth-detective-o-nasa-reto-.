"""
SI-assisted: claude-omni-1 (Claude Sonnet 5.5)
RONDA 4 — Verificación exhaustiva de Interfaz (claude-omni-1)
Cubre las tres tareas del §4:
  Tarea 1 (dom 02:00): 9 comprobaciones con capturas individuales
  Tarea 2 (dom 04:00): "Planned by: rules / fine-tuned model" + variables planned disabled con not_loaded
  Tarea 3 (dom 04:00): Vista móvil a 390px, cero scroll horizontal, mapa y gráfica utilizables
Todas las capturas se guardan en docs/media/r4/ y se actualizan las oficiales en docs/media/.
"""

import os
import sys
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_R4 = os.path.join(BASE_DIR, "docs", "media", "r4")
OUT_MEDIA = os.path.join(BASE_DIR, "docs", "media")
os.makedirs(OUT_R4, exist_ok=True)
os.makedirs(OUT_MEDIA, exist_ok=True)
URL = "http://127.0.0.1:8000/"
CSV = os.path.join(BASE_DIR, "data", "raw", "giovanni", "T2M__amazonia.csv")

results = []

def verdict(name, ok, detail=""):
    results.append((name, ok, detail))
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name} :: {detail}")

def shot(page, rel_path):
    page.wait_for_timeout(350)
    p = os.path.join(OUT_R4, rel_path)
    page.screenshot(path=p)
    print(f"  screenshot -> {p}")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # ================================================================
        # SECCION A: Desktop (1600x900) - Tareas 1 y 2
        # ================================================================
        print("\n=== DESKTOP 1600x900 (Tareas 1 y 2) ===")
        ctx = browser.new_context(viewport={"width": 1600, "height": 900})
        page = ctx.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(1000)
        page.evaluate("() => window.__etd.setLang('en')")
        page.wait_for_timeout(600)

        # TAREA 2.A: Selector de variables - Variables planned deshabilitadas
        print("\n-- Check planned variables in select (Rule 19) --")
        planned_info = page.evaluate("""() => {
          const select = document.getElementById('variable-select');
          if (!select) return { found: false };
          const opts = Array.from(select.options);
          const disabled = opts.filter(o => o.disabled);
          const plannedGroup = select.querySelector('optgroup[label*="Planned"], optgroup[label*="Planificadas"]');
          return {
            total: opts.length,
            disabledCount: disabled.length,
            disabledNames: disabled.slice(0, 4).map(o => o.textContent),
            hasPlannedGroup: Boolean(plannedGroup),
            firstSelectableValue: opts.find(o => !o.disabled)?.value
          };
        }""")
        verdict("T2 planned disabled count >= 10", planned_info.get("disabledCount", 0) >= 10,
                f"found {planned_info.get('disabledCount')} disabled opts")
        first_disabled = planned_info.get("disabledNames", [""])[0] if planned_info.get("disabledNames") else ""
        verdict("T2 planned has not-loaded label", "upload" in first_disabled.lower() or "not loaded" in first_disabled.lower(),
                first_disabled)

        # TAREA 2.B: Planificador IA con atribución de "Planned by: rules / LoRA"
        print("\n-- Check AI Detective plan attribution --")
        page.evaluate("""() => {
          window.__etd.setMode('single');
          const input = document.getElementById('detective-input');
          input.value = 'How is air temperature changing in Lima?';
          document.getElementById('detective-ask-btn').click();
        }""")
        page.wait_for_selector("#detective-plan-card:not([hidden])", timeout=15000)
        page.wait_for_timeout(1000)
        shot(page, "plan_attribution.png")
        # Also copy to docs/media/ for official submissions
        page.screenshot(path=os.path.join(OUT_MEDIA, "plan_attribution.png"))

        plan_attr = page.evaluate("""() => {
          const badge = document.getElementById('plan-meta-badge');
          const note = document.getElementById('plan-note-text');
          const intent = document.getElementById('plan-intent-text');
          return {
            badgeText: badge ? badge.textContent.trim() : '',
            badgeVisible: badge ? !badge.hidden : false,
            badgeClass: badge ? badge.className : '',
            noteText: note ? note.textContent.trim() : '',
            noteHidden: note ? note.hidden : true,
            intentText: intent ? intent.textContent.trim() : ''
          };
        }""")
        badge_text = plan_attr.get("badgeText", "")
        has_planned_by = "planned by" in badge_text.lower()
        is_rules_or_lora = "rules" in badge_text.lower() or "lora" in badge_text.lower() or "fine-tuned" in badge_text.lower()
        verdict("T2 Planned by attribution present", has_planned_by and is_rules_or_lora, f"'{badge_text}'")

        # Confirm and run the plan
        page.evaluate("() => document.getElementById('plan-confirm-btn').click()")
        page.wait_for_selector("#result-root:not([hidden])", timeout=20000)
        page.wait_for_timeout(1500)

        # TAREA 1.1: Citas vinculadas con título y editor, sin (NASA) fijo
        page.evaluate("""() => document.getElementById('explain-plate')
          ? document.getElementById('explain-plate').scrollIntoView({behavior:'instant', block:'start'})
          : null""")
        page.wait_for_selector("#explain-plate .ai-badge", timeout=15000)
        page.wait_for_timeout(600)
        shot(page, "citations_verified.png")
        cites = page.eval_on_selector_all("#explain-plate a[href]", "els => els.map(e => ({text: e.textContent.trim().slice(0,80), href: e.getAttribute('href')}))")
        verdict("T1 citations linked", len(cites) >= 1, f"{len(cites)} links; {cites[:2]}")
        has_fixed_nasa = any("(NASA)" in c.get("text", "") for c in cites)
        verdict("T1 no fixed (NASA) label", not has_fixed_nasa, "")

        # TAREA 1.2: Rótulo extractivo sin IA generativa
        badge_text = page.evaluate("() => document.querySelector('#explain-plate .ai-badge')?.textContent || ''")
        has_extractive = "no generative ai" in badge_text.lower() or "sin ia generativa" in badge_text.lower()
        verdict("T1 extractive label present", has_extractive, f"badge='{badge_text}'")

        # TAREA 1.3: Panel de pruebas que discrepan
        page.evaluate("() => window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
        has_disagree = page.evaluate("""() => {
          return /Mann-Kendall|Kendall|tests_agree|disagree|discrepan/i.test(document.body.innerText);
        }""")
        verdict("T1 tests disagree panel visible", has_disagree, "")

        # TAREA 1.4: Galería de 7 casos
        page.evaluate("() => window.__etd.setMode('cases')")
        page.wait_for_timeout(1000)
        shot(page, "cases_gallery.png")
        page.screenshot(path=os.path.join(OUT_MEDIA, "cases_gallery.png"))
        cases_count = page.evaluate("() => document.querySelectorAll('#cases-list .case-btn, .case-btn').length")
        verdict("T1 gallery has 7 cases", cases_count >= 7, f"found {cases_count}")

        # TAREA 1.5: Atlas global
        page.evaluate("""() => {
          window.__etd.setMode('trendmap');
          const btn = document.getElementById('btn-load-atlas');
          if (btn) btn.click();
        }""")
        page.wait_for_selector("#trendmap-root:not([hidden])", timeout=20000)
        page.wait_for_timeout(1500)
        shot(page, "atlas_loaded.png")
        has_atlas_stats = page.evaluate("() => /Grid cells|celdas|FDR/i.test(document.getElementById('trendmap-root')?.innerText || '')")
        verdict("T1 atlas rendered", has_atlas_stats, "")

        # TAREA 1.6: Variables sin lugar (GISTEMP y Hielo marino)
        for vid, name in [("GISTEMP_TANOM", "gistemp"), ("SEAICE_EXTENT_N", "seaice")]:
            page.evaluate(f"""() => {{
              window.__etd.setMode('single');
              const sel = document.getElementById('variable-select');
              sel.value = '{vid}';
              window.__etd.onVariableChange?.();
              document.getElementById('investigate-btn').click();
            }}""")
            page.wait_for_selector("#result-root:not([hidden])", timeout=20000)
            page.wait_for_timeout(800)
            shot(page, f"no_place_{name}.png")
            err = page.evaluate("() => document.getElementById('error-box') ? document.getElementById('error-box').innerText : ''")
            verdict(f"T1 {vid} no coordinates required", "400" not in err and "coordinates" not in err.lower(), f"err={err[:40]}")

        # TAREA 1.7: Subida de CSV de Giovanni
        if os.path.exists(CSV):
            with page.expect_response(lambda r: "/api/analyze/upload" in r.url, timeout=25000):
                page.locator("#csv-file-input").set_input_files(CSV)
            page.wait_for_timeout(1500)
            shot(page, "giovanni_csv_upload.png")
            page.screenshot(path=os.path.join(OUT_MEDIA, "giovanni_csv_upload.png"))
            prov = page.evaluate("() => document.getElementById('provenance-plate')?.innerText || document.getElementById('result-root')?.innerText || ''")
            verdict("T1 CSV upload analyzed", "upload" in prov.lower() or "giovanni" in prov.lower() or "t2m" in prov.lower() or "amazonia" in prov.lower(), prov[:80].replace("\n", " "))
        else:
            verdict("T1 CSV upload", False, "file missing")

        ctx.close()

        # ================================================================
        # SECCION B: Mobile Viewport 390px (Tarea 3)
        # ================================================================
        print("\n=== MOBILE VIEWPORT 390x844 (Tarea 3) ===")
        m_ctx = browser.new_context(viewport={"width": 390, "height": 844})
        m_page = m_ctx.new_page()
        m_page.goto(URL, wait_until="networkidle")
        m_page.wait_for_timeout(1000)
        m_page.evaluate("() => window.__etd.setLang('en')")
        m_page.wait_for_timeout(600)

        # 1. No horizontal scroll on initial screen
        sw_init = m_page.evaluate("() => document.documentElement.scrollWidth")
        cw_init = m_page.evaluate("() => document.documentElement.clientWidth")
        diff_init = sw_init - cw_init
        verdict("T3 mobile initial no horizontal scroll", diff_init <= 1, f"scrollWidth={sw_init}, clientWidth={cw_init}, diff={diff_init}")
        shot(m_page, "mobile_390_initial.png")

        # 2. Check map dimensions are usable (> 300 x > 200)
        map_dim = m_page.evaluate("""() => {
          const el = document.getElementById('map');
          const r = el.getBoundingClientRect();
          return { w: Math.round(r.width), h: Math.round(r.height) };
        }""")
        map_usable = map_dim.get("w", 0) >= 300 and map_dim.get("h", 0) >= 200
        verdict("T3 mobile map usable", map_usable, f"{map_dim['w']}x{map_dim['h']}px")

        # 3. Investigate a case on mobile
        m_page.evaluate("""() => {
          window.__etd.setPoint(-12.05, -77.03, 'Lima, Peru');
          document.getElementById('investigate-btn').click();
        }""")
        m_page.wait_for_selector("#result-root:not([hidden])", timeout=20000)
        m_page.wait_for_timeout(1500)

        # 4. No horizontal scroll with full results rendered
        sw_res = m_page.evaluate("() => document.documentElement.scrollWidth")
        cw_res = m_page.evaluate("() => document.documentElement.clientWidth")
        diff_res = sw_res - cw_res
        verdict("T3 mobile results no horizontal scroll", diff_res <= 1, f"scrollWidth={sw_res}, clientWidth={cw_res}, diff={diff_res}")

        # 5. Check chart dimensions on mobile (using #trend-chart canvas)
        chart_dim = m_page.evaluate("""() => {
          const el = document.getElementById('trend-chart');
          if (!el) return { w: 0, h: 0 };
          const r = el.getBoundingClientRect();
          return { w: Math.round(r.width), h: Math.round(r.height) };
        }""")
        chart_usable = chart_dim.get("w", 0) >= 300 and chart_dim.get("h", 0) >= 200
        verdict("T3 mobile chart usable", chart_usable, f"{chart_dim['w']}x{chart_dim['h']}px")

        # 6. Capture mobile overview
        shot(m_page, "mobile_390_overview.png")
        m_page.screenshot(path=os.path.join(OUT_MEDIA, "mobile_390_overview.png"))

        # Scroll to chart on mobile
        m_page.evaluate("""() => {
          const el = document.querySelector('.chart-plate');
          if (el) el.scrollIntoView({behavior:'instant', block:'center'});
        }""")
        m_page.wait_for_timeout(400)
        shot(m_page, "mobile_390_chart.png")

        m_ctx.close()
        browser.close()

        # ================================================================
        # RESUMEN FINAL
        # ================================================================
        print("\n" + "="*60)
        print("               RESUMEN FINAL DE LA RONDA 4")
        print("="*60)
        n_pass = sum(1 for _, ok, _ in results if ok)
        total = len(results)
        print(f"Total: {n_pass}/{total} verificaciones en PASS ({n_pass/total*100:.1f}%)\n")
        all_ok = (n_pass == total)
        for name, ok, detail in results:
            tag = "PASS" if ok else "FAIL"
            print(f"  [{tag}] {name}")
        return all_ok

if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)
