"""Capture the REAL deployed app (English UI) for the slides and the video."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://huiracochaia.soulgeit.com/"
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1600, "height": 900}, device_scale_factor=1, locale="en-US")
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

    # 1) the note + "how it works" panel (open on a first visit)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_selector("#intro-grid .intro-card", timeout=20000)
    page.locator("#intro").screenshot(path=str(OUT / "huiracocha_about.png"))

    # 2) a real conversation: question -> plan -> real NASA series -> verdict
    page.locator("#intro-how").evaluate("el => { el.open = false; }")
    page.fill("#detective-input", "Is Lima getting hotter?")
    page.press("#detective-input", "Enter")
    page.wait_for_selector("text=Result ·", timeout=60000)
    page.wait_for_selector("#explain-text:not(:empty)", timeout=30000)
    page.wait_for_timeout(1500)
    page.locator(".chat-console").screenshot(path=str(OUT / "huiracocha_chat.png"))

    # 3) the verdict + chart column (the functional app)
    page.evaluate("document.getElementById('results').scrollIntoView({block: 'start'})")
    page.wait_for_timeout(1200)
    page.screenshot(path=str(OUT / "huiracocha_verdict.png"))

    # 4) all-variables scan for a Peruvian city
    page.evaluate("document.querySelector('.chat-console').scrollIntoView({block: 'start'})")
    page.get_by_role("button", name="Huancayo", exact=True).click()
    page.wait_for_selector("text=changes confirmed", timeout=90000)
    page.wait_for_timeout(1200)
    box = page.locator("#scan-root").bounding_box()
    page.evaluate("document.getElementById('scan-root').scrollIntoView({block: 'start'})")
    page.wait_for_timeout(800)
    page.screenshot(path=str(OUT / "huiracocha_scan.png"))
    print("console/page errors:", errors[:5])
    # 5) phone view of the live app (390 px wide, 2x for a crisp phone mock-up)
    mobile = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, locale="en-US",
                                 is_mobile=True, has_touch=True)
    m = mobile.new_page()
    m.goto(URL, wait_until="networkidle")
    m.wait_for_selector("#intro-grid .intro-card", timeout=20000)
    m.locator("#intro-how").evaluate("el => { el.open = false; }")
    m.evaluate("document.querySelector('.chat-console').scrollIntoView({block: 'start'})")
    m.wait_for_timeout(800)
    m.screenshot(path=str(OUT / "huiracocha_mobile_390.png"))
    overflow = m.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    print("mobile horizontal overflow px:", overflow)
    browser.close()
print("captures:", sorted(f.name for f in OUT.glob("huiracocha_*.png")))
