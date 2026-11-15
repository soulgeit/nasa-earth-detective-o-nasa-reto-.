# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Planner evaluation on the golden questions:  python -m src.detective.rag.eval_plan

RONDA_3 §4 (claude-omni-2, task 4): docs/EVAL_IA.md must show the 50 questions in
`data/knowledge/golden_questions.jsonl` run through the real planner, and through
the LoRA when one exists. Only real executions: if the adapter is missing the LoRA
column says "not available", it never gets a number.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
import time
from typing import Any

from ..config import SETTINGS
from ..planner import plan


def load_questions() -> list[dict[str, Any]]:
    path = SETTINGS.knowledge_dir / "golden_questions.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing")
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def evaluate(*, planner: str | None = None, limit: int | None = None) -> dict[str, Any]:
    """Run every question through ``plan()`` and score the variable choice."""
    from .. import config as config_module
    import src.detective.planner as planner_module

    if planner:
        # "local-lora" switches the real adapter on; anything else leaves the
        # configured planner untouched.
        object.__setattr__(config_module.SETTINGS, "ai_mode", "full")
        object.__setattr__(config_module.SETTINGS, "planner_model", planner)
        object.__setattr__(planner_module.SETTINGS, "ai_mode", "full")
        object.__setattr__(planner_module.SETTINGS, "planner_model", planner)

    rows = load_questions()
    if limit:
        rows = rows[:limit]
    correct = 0
    intents = collections.Counter()
    planners = collections.Counter()
    failures: list[dict[str, Any]] = []
    started = time.perf_counter()

    for row in rows:
        question = row["question"]
        lang = row.get("lang", "es")
        expected = set(row.get("expected_variable_ids") or [])
        result = plan(question, lang=lang)
        got = set(result.get("variable_ids") or [])
        intent = str(result.get("intent"))
        intents[intent] += 1
        planners[str(result.get("planner") or result.get("mode"))] += 1
        hit = bool(expected & got) and intent in ("investigate", "compare", "define")
        if hit:
            correct += 1
        else:
            failures.append({
                "question": question,
                "lang": lang,
                "intent": intent,
                "got": sorted(got),
                "expected": sorted(expected),
                "planner": result.get("planner") or result.get("mode"),
            })

    return {
        "mode": SETTINGS.ai_mode,
        "n": len(rows),
        "correct": correct,
        "accuracy": round(correct / len(rows), 4) if rows else 0.0,
        "by_intent": dict(intents),
        "by_planner": dict(planners),
        "seconds": round(time.perf_counter() - started, 1),
        "failures": failures,
    }


def markdown(result: dict[str, Any], *, planner_label: str) -> str:
    lines = [
        f"| Planificador / Planner | Acierto de variable / Variable accuracy | Preguntas |",
        "|---|---|---|",
        f"| {planner_label} | {result['correct']}/{result['n']} = {result['accuracy']:.3f} | {result['n']} |",
        "",
        "Intenciones detectadas / Detected intents: "
        + ", ".join(f"`{k}` {v}" for k, v in sorted(result["by_intent"].items())),
        "",
        "Quién planificó / Who planned: " + ", ".join(f"`{k}` {v}" for k, v in sorted(result["by_planner"].items())),
        "",
    ]
    if result["failures"]:
        lines.append("Fallos / Failures:")
        lines.append("")
        lines.append("| Pregunta / Question | Idioma | Intención | Devuelto / Got | Esperado / Expected |")
        lines.append("|---|---|---|---|---|")
        for f in result["failures"]:
            lines.append(
                f"| {f['question']} | {f['lang']} | `{f['intent']}` | `{', '.join(f['got']) or '—'}` | "
                f"`{', '.join(f['expected']) or '—'}` |"
            )
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate the planner on the golden questions.")
    parser.add_argument("--planner", default=None, help="e.g. local-lora; default: as configured")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = evaluate(planner=args.planner, limit=args.limit)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    label = args.planner or "rules"
    print(markdown(result, planner_label=label))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
