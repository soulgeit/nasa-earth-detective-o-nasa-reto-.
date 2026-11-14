# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Runtime configuration for the AI detective (contracts §11).

Everything is read from the environment with safe defaults so the module can be
imported in tests without a .env file (rule: AI_MODE=extractive must always work).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

VALID_MODES = ("full", "extractive", "off")
VALID_LANGS = ("es", "en")


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _mode() -> str:
    raw = _env("AI_MODE", "extractive").lower()
    if raw not in VALID_MODES:
        # Never crash on a typo: fall back to the safe mode and expose it.
        return "extractive"
    return raw


@dataclass(frozen=True)
class Settings:
    ai_mode: str
    llm_base_url: str
    planner_model: str
    explain_model: str
    embed_base_url: str
    embed_model: str
    data_dir: Path
    catalog_dir: Path
    knowledge_dir: Path
    index_dir: Path
    request_timeout: float

    @property
    def llm_enabled(self) -> bool:
        return self.ai_mode == "full"

    @property
    def embeddings_enabled(self) -> bool:
        # Embeddings are allowed in `full`; in `extractive`/`off` we never call out.
        return self.ai_mode == "full" and bool(self.embed_model)


def load_settings() -> Settings:
    data_dir = Path(_env("DATA_DIR") or REPO_ROOT / "data")
    return Settings(
        ai_mode=_mode(),
        llm_base_url=_env("LLM_BASE_URL", "http://localhost:11434/v1"),
        planner_model=_env("PLANNER_MODEL"),
        explain_model=_env("EXPLAIN_MODEL"),
        embed_base_url=_env("EMBED_BASE_URL", "http://localhost:11434"),
        embed_model=_env("EMBED_MODEL"),
        data_dir=data_dir,
        catalog_dir=data_dir / "catalog",
        knowledge_dir=data_dir / "knowledge",
        index_dir=data_dir / "cache" / "rag",
        request_timeout=float(_env("AI_HTTP_TIMEOUT", "60") or 60),
    )


SETTINGS = load_settings()
