# SI-assisted: cfable (Claude Sonnet 5.5)
"""The guided demo opens far below the chat; a floating button takes the visitor there (it looked as if nothing happened)."""

from __future__ import annotations

from pathlib import Path

UI = Path(__file__).resolve().parents[2] / "src" / "ui"
HTML = (UI / "index.html").read_text(encoding="utf-8")
APP = (UI / "app.js").read_text(encoding="utf-8")
I18N = (UI / "i18n.js").read_text(encoding="utf-8")
CSS = (UI / "styles.css").read_text(encoding="utf-8")


def test_the_button_exists_hidden_and_translated_in_both_languages():
    assert 'id="btn-demo-scroll"' in HTML and 'data-i18n="demo.btn.scroll"' in HTML
    button = HTML[HTML.index('id="btn-demo-scroll"'): HTML.index("DEMO NARRATIVE BANNER")]
    assert " hidden " in button, "it starts hidden: it only matters while the demo runs"
    assert I18N.count("'demo.btn.scroll'") == 2, "one string per language"
    assert "Go to the demo" in I18N and "Ir a la demo" in I18N


def test_the_demo_start_scrolls_to_the_banner_and_updates_the_button():
    start = APP[APP.index("function startDemo()"): APP.index("function stopDemo()")]
    assert "scrollIntoView" in start and "updateDemoScrollButton()" in start
    stop = APP[APP.index("function stopDemo()"): APP.index("function stopDemo()") + 400]
    assert "updateDemoScrollButton()" in stop, "leaving the demo must hide the button"


def test_the_button_follows_the_scroll_and_scrolls_back_to_the_banner():
    assert "window.addEventListener('scroll', updateDemoScrollButton" in APP
    assert "$('#btn-demo-scroll')?.addEventListener('click'" in APP
    assert ".demo-scroll-btn" in CSS and ".demo-scroll-btn[hidden]" in CSS
