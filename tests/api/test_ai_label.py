# SI-assisted: cfable (Claude Sonnet 5.5)
"""The AI-generated logo is declared and carries a visible mark wherever the app shows it (Space Apps rule:
images generated with SI carry a visible watermark and are acknowledged in the text)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "src" / "ui"
HTML = (UI / "index.html").read_text(encoding="utf-8")
CHAT = (UI / "chat.js").read_text(encoding="utf-8")


def test_the_header_logo_has_a_visible_ai_generated_label_next_to_it():
    wrap = HTML[HTML.index('class="brand-logo-wrap"'): HTML.index('class="brand-titles"')]
    assert "huiracocha_ia_navbar_128.png" in wrap
    assert '<span class="ai-mark">AI-generated</span>' in wrap
    assert "generated with AI" in wrap, "the alt text must say it too"
    assert ".ai-mark" in (UI / "styles.css").read_text(encoding="utf-8")


def test_the_social_preview_is_the_marked_copy():
    match = re.search(r'property="og:image" content="[^"]*/assets/([\w.]+)"', HTML)
    assert match and match.group(1) == "huiracocha_ia_og_ai.png"
    assert (UI / "assets" / "huiracocha_ia_og_ai.png").exists()


def test_the_marked_preview_really_has_the_text_painted_in_its_bottom_strip():
    pil = pytest.importorskip("PIL.Image")
    from PIL import ImageChops

    original = pil.open(UI / "assets" / "huiracocha_ia_dark_centered.png").convert("RGB")
    marked = pil.open(UI / "assets" / "huiracocha_ia_og_ai.png").convert("RGB")
    assert original.size == marked.size
    box = ImageChops.difference(original, marked).getbbox()
    assert box is not None and box[1] >= marked.size[1] * 0.85, "the mark must sit in the bottom strip and nowhere else"


def test_the_footer_and_the_docs_say_the_logo_was_generated_with_ai():
    assert "the logo was generated with AI (Antigravity)" in CHAT
    assert "el logo fue generado con IA (Antigravity)" in CHAT
    for rel in ("docs/SUBMISSION.md", "docs/AI_USE_LOG.md", "src/ui/assets/README.md"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "Antigravity" in text and "logo" in text.lower(), rel
    submission = (ROOT / "docs" / "SUBMISSION.md").read_text(encoding="utf-8")
    assert "No images or video were generated with SI;" not in submission, "false since the logo is AI-generated"
    assert "except the project logo" in submission
