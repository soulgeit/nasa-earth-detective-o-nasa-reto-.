# SI-assisted: cfable (Claude Sonnet 5.5)
"""RONDA_7: the "how it works" facts, the scan route and the console wiring.

The about payload may never say more than the deployment has, and its fixed
LoRA figures must stay equal to the model card they are copied from.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "src" / "ui"


@pytest.fixture()
def client() -> TestClient:
    from src.api import modules

    modules.clear_cache()
    import src.api.main as main_mod

    main_mod.limiter.reset()
    return TestClient(main_mod.app)


def test_about_numbers_come_from_the_live_corpus(client: TestClient) -> None:
    from src.detective.rag import corpus_documents

    body = client.get("/api/ai/about", params={"lang": "en"}).json()
    docs = corpus_documents()
    assert body["schema"] == "about/1"
    assert body["corpus"]["documents"] == len(docs)
    assert body["corpus"]["publishers"] == len({d.publisher for d in docs if d.publisher})
    assert body["corpus"]["sources"] == len({d.url for d in docs if d.url})
    assert body["corpus"]["skipped_rows"] == 0, "a lane pushed rows the app skips"
    cities = {c["id"]: c for c in body["corpus"]["cities"]}
    assert set(cities) == {"lima", "huancayo", "andahuaylas", "ica", "ayacucho"}
    for city in cities.values():
        assert city["docs"] == city["es"] + city["en"] > 0
    assert body["catalog"]["available"] >= 35


def test_about_never_claims_a_model_the_server_does_not_run(client: TestClient, monkeypatch) -> None:
    from src.detective import about_facts as about_mod

    body = client.get("/api/ai/about").json()
    deployment = body["deployment"]
    assert deployment["generative_text"] is False
    lora = deployment["lora"]
    assert lora["active"] == (lora["configured"] and lora["runtime_present"] and lora["adapter_present"])
    assert deployment["engine"] == ("lora+rag" if lora["active"] else "rules+rag")
    assert deployment["planner"] == ("lora" if lora["active"] else "rules")

    # An extractive server (the public one) is never reported as a LoRA server.
    about_mod.reset_cache()
    cfg = about_mod.SETTINGS.__class__(**{**about_mod.SETTINGS.__dict__, "ai_mode": "extractive", "planner_model": ""})
    monkeypatch.setattr(about_mod, "SETTINGS", cfg)
    try:
        assert about_mod.about(lang="en")["deployment"]["engine"] == "rules+rag"
    finally:
        about_mod.reset_cache()


def test_lora_figures_equal_the_model_card() -> None:
    """The panel copies these numbers; if the card changes, the panel must not lie."""
    from src.detective.about_facts import LORA_FACTS

    card = (ROOT / "src" / "ml" / "MODEL_CARD.md").read_text(encoding="utf-8")
    assert LORA_FACTS["sha256"] in card
    assert f"{LORA_FACTS['trainable_params']:,}" in card
    assert f"{LORA_FACTS['train_examples']:,}" in card
    assert f"{LORA_FACTS['train_steps']} steps" in card
    assert "RTX 4070 SUPER" in card and "RTX 4070 SUPER" in LORA_FACTS["hardware"]
    assert LORA_FACTS["base_model"] in card
    rq = LORA_FACTS["reference_questions"]
    assert f"{rq['rules']} / {rq['total']}" in card
    assert f"{rq['lora_gpu']} / {rq['total']}" in card
    assert f"{rq['lora_cpu']} / {rq['total']}" in card
    assert f"{LORA_FACTS['synthetic_cases']['exact_variable_pct']['lora']}%" in card


def test_the_resources_are_the_platforms_of_the_challenge(client: TestClient) -> None:
    resources = client.get("/api/ai/about", params={"lang": "es"}).json()["resources"]
    urls = {r["url"] for r in resources}
    for expected in ("https://giovanni.gsfc.nasa.gov/giovanni/", "https://appeears.earthdatacloud.nasa.gov/",
                     "https://www.ncei.noaa.gov/cdo-web/", "https://climexp.knmi.nl/"):
        assert any(u and u.rstrip("/") == expected.rstrip("/") for u in urls), expected
    assert all((r["url"] or "").startswith("https://") for r in resources)
    assert len(urls) == len(resources), "one entry per page"


# --- the console must find every element it drives -----------------------------

def _ids_used_by_chat_js() -> set[str]:
    source = (UI / "chat.js").read_text(encoding="utf-8")
    ids = set(re.findall(r"\$\('#([A-Za-z0-9_-]+)'\)", source))
    ids |= set(re.findall(r"getElementById\('([A-Za-z0-9_-]+)'\)", source))
    ids |= {i for i in re.findall(r"\['([a-z-]+-root|empty-state|error-state)'", source)}
    return ids


def test_every_element_chat_js_drives_exists_in_the_page() -> None:
    html = (UI / "index.html").read_text(encoding="utf-8")
    present = set(re.findall(r'id="([A-Za-z0-9_-]+)"', html))
    missing = sorted(i for i in _ids_used_by_chat_js() if i not in present)
    assert not missing, f"chat.js needs elements the page lost: {missing}"


def test_scripts_load_in_order_and_share_one_version() -> None:
    html = (UI / "index.html").read_text(encoding="utf-8")
    order = [m.group(1) for m in re.finditer(r'<script src="((?:i18n|chat|app)\.js)\?v=([\w.]+)"', html)]
    assert order == ["i18n.js", "chat.js", "app.js"], order
    versions = set(re.findall(r'(?:styles\.css|i18n\.js|chat\.js|app\.js)\?v=([\w.]+)', html))
    assert len(versions) == 1, f"assets carry different cache-busting versions: {versions}"


def test_the_old_narrow_box_is_gone_and_one_textarea_remains() -> None:
    html = (UI / "index.html").read_text(encoding="utf-8")
    assert html.count('id="detective-input"') == 1
    assert 'id="detective-plan-card"' not in html


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_the_scripts_parse() -> None:
    for name in ("chat.js", "app.js", "i18n.js"):
        result = subprocess.run(["node", "--check", str(UI / name)], capture_output=True, text=True)
        assert result.returncode == 0, f"{name}: {result.stderr[:300]}"


def test_every_chat_string_exists_in_both_languages() -> None:
    source = (UI / "chat.js").read_text(encoding="utf-8")
    en = source[source.index("const EN = {"): source.index("const ES = {")]
    es = source[source.index("const ES = {"): source.index("Object.assign(I18N.STRINGS.en")]
    keys_en = set(re.findall(r"^  '([\w.]+)':", en, re.M))
    keys_es = set(re.findall(r"^  '([\w.]+)':", es, re.M))
    assert keys_en == keys_es, f"only in EN: {sorted(keys_en - keys_es)}; only in ES: {sorted(keys_es - keys_en)}"
    used = set(re.findall(r"\bt[c]?\('([\w.]+)'", source))
    undefined = sorted(k for k in used if k not in keys_en)
    # keys built from a template (chat.ex.N, chat.topic.X, intro.step.N) must exist for every value
    assert {f"chat.ex.{i}" for i in range(1, 6)} <= keys_en
    assert {f"intro.step.{i}" for i in range(1, 7)} <= keys_en
    for topic in ("rain", "temp", "frost", "wind", "uv", "soil"):
        assert {f"chat.topic.{topic}", f"chat.topic.{topic}.l"} <= keys_en
    assert not undefined, f"strings used by chat.js but never defined: {undefined}"


def test_the_static_build_carries_the_console_and_its_assets(tmp_path: Path) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("build_static", ROOT / "scripts" / "build_static.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    dist = tmp_path / "dist"
    module.DIST = dist
    module.copy_ui()
    assert (dist / "chat.js").exists()
    assert (dist / "assets" / "huiracocha_ia_navbar_128.png").exists()
    html = (dist / "index.html").read_text(encoding="utf-8")
    assert "chat.js" in html


def test_scan_route_is_registered(client: TestClient) -> None:
    paths = {route.path for route in client.app.routes}
    assert {"/api/scan", "/api/ai/chat", "/api/ai/about"} <= paths
