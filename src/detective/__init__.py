# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""EarthTrend Detective — the AI detective (contracts §6).

Public surface, exactly as agreed with the other lanes:

    retrieve(query, *, lang="es", k=6, types=None) -> list[dict]
    plan(question, *, lang="es") -> dict            # InvestigationPlan, contract §10
    chat(message, *, lang=None, context=None) -> dict   # conversational turn (RONDA_7)
    scout(lat, lon, *, lang="es") -> dict           # candidate variables for a place
    explain(analysis, *, level="school", lang="es") -> dict
    geocode(q) -> list[dict]                        # [{"name","country","lat","lon","bbox"}]

The former 4-option dictionary wizard is gone: it fabricated regions and variables.
"""

from __future__ import annotations

from .rag import retrieve as _retrieve

__all__ = ["retrieve", "plan", "chat", "about", "scout", "explain", "geocode", "__version__"]

__version__ = "2.0.0"


def retrieve(query: str, *, lang: str = "es", k: int = 6, types=None):
    """Documents from the verified corpus, each with ``score``, ``title``, ``url``."""
    return _retrieve(query, lang=lang, k=k, types=types)


def plan(question: str, *, lang: str = "es"):
    from .planner import plan as _plan

    return _plan(question, lang=lang)


def chat(message: str, *, lang: str | None = None, context: dict | None = None):
    """One conversational turn with Huiracocha IA (RONDA_7): reply, plan and sources."""
    # The module is NOT called chat.py on purpose: importing a submodule named
    # like this function would replace the function on the package with the module.
    from .conversation import chat as _chat

    return _chat(message, lang=lang, context=context)


def about(*, lang: str = "es"):
    """Live facts for the "how Huiracocha IA works" panel (corpus, cities, LoRA, deployment)."""
    # NOT called about.py: a submodule named like this function would replace the
    # function on the package the first time it is imported (the 2nd request would 503).
    from .about_facts import about as _about

    return _about(lang=lang)


def scout(lat: float, lon: float, *, lang: str = "es"):
    from .scouting import scout as _scout

    return _scout(lat, lon, lang=lang)


def explain(analysis: dict, *, level: str = "school", lang: str = "es"):
    from .narrative import explain as _explain

    return _explain(analysis, level=level, lang=lang)


def geocode(q: str):
    from .gazetteer import geocode as _geocode

    return _geocode(q)
