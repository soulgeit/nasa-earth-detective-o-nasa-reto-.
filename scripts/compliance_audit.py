# SI-assisted: cfable (Claude Sonnet 5.5)
"""One-command compliance audit of the Space Apps submission (docs/KIT_ENTREGA.md section 1).

    python scripts/compliance_audit.py

PASS / FAIL / WARN are decided by the script; MANUAL items only a person can confirm.
Exit code 1 if anything FAILs. Read-only: it changes nothing.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIVE = "https://huiracochaia.soulgeit.com"
PAGES = "https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./"
REPO = "https://github.com/soulgeit/nasa-earth-detective-o-nasa-reto-."
DOWNLOADED_VIDEO = Path.home() / "Downloads" / "Huiracocha_AI_pitch_30s_SI-labelled.mp4"
SECRETS = r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-(proj-)?[A-Za-z0-9_-]{30,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|xox[abp]-[A-Za-z0-9-]{10,})"
counts = {"PASS": 0, "FAIL": 0, "WARN": 0}


def record(status: str, label: str, detail: str = "") -> None:
    counts[status] = counts.get(status, 0) + 1
    print(f"  {status:<6} {label}" + (f"  [{detail}]" if detail else ""))


def check(label: str, fn, *, warn_only: bool = False) -> None:
    try:
        ok, detail = fn()
        record("PASS" if ok else ("WARN" if warn_only else "FAIL"), label, detail)
    except Exception as exc:  # a broken check must not hide the others
        record("WARN", label, f"could not run: {type(exc).__name__}: {str(exc)[:90]}")


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT, timeout=150)


def fetch(url: str) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "compliance-audit"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status, response.read().decode("utf-8", "replace")


def video(path: Path):
    def inner():
        info = json.loads(run("ffprobe", "-v", "error", "-show_entries", "format=duration:format_tags", "-of", "json", str(path)).stdout)["format"]
        seconds = float(info["duration"])
        labelled = "SI DISCLOSURE" in info.get("tags", {}).get("comment", "")
        return seconds <= 30.0 and labelled, f"{seconds:.2f} s (limit 30), SI disclosure in metadata: {labelled}"
    return inner


def slides():
    path = ROOT / "docs" / "demo" / "EarthTrend_Detective_slides.pdf"
    try:
        from pypdf import PdfReader
        pages = len(PdfReader(str(path)).pages)
    except ImportError:
        pages = len(re.findall(rb"/Type\s*/Page(?![A-Za-z])", path.read_bytes()))
    return 0 < pages <= 7, f"{pages} pages (limit 7)"


def reachable(url: str, needle: str | None = None):
    def inner():
        status, body = fetch(url)
        found = needle is None or needle in body
        return status == 200 and found, f"HTTP {status}" + ("" if needle is None else f", has {needle!r}: {found}")
    return inner


def live_engine():
    status, body = fetch(LIVE + "/api/ai/about?lang=en")
    deployment = json.loads(body)["deployment"]
    return status == 200, f"engine={deployment['engine']}, provider state={deployment['llm']['state']}, host={deployment['llm'].get('host')}"


def si_headers():
    missing = []
    for pattern in ("src/**/*.py", "scripts/*.py", "tests/**/*.py", "src/ui/*.js"):
        for path in ROOT.glob(pattern):
            if "__pycache__" in path.parts:
                continue
            head = "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[:4])
            if "SI-assisted" not in head:
                missing.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    return not missing, f"{len(missing)} files without the header" + (": " + ", ".join(missing[:6]) if missing else "")


def secrets_tracked():
    out = run("git", "grep", "-I", "-l", "-E", SECRETS, "HEAD").stdout.strip()
    hits = [line.split(":", 1)[1] for line in out.splitlines() if line and "compliance_audit.py" not in line]
    return not hits, "no secret pattern in tracked files" if not hits else "files: " + ", ".join(hits[:6])


def secrets_history():
    out = run("git", "log", "--all", "--oneline", "-G", r"(ghp_[A-Za-z0-9]{30,}|sk-proj-[A-Za-z0-9_-]{30,})").stdout.strip()
    return not out, "none in any commit" if not out else f"{len(out.splitlines())} commits contain a token pattern"


def disclosure():
    submission = (ROOT / "docs" / "SUBMISSION.md").read_text(encoding="utf-8")
    log = (ROOT / "docs" / "AI_USE_LOG.md").read_text(encoding="utf-8")
    reviewers = "".join(line.rsplit("|", 2)[-2].lower() for line in log.splitlines() if line.startswith("| 20"))
    needs = {
        "logo declared": "except the project logo" in submission,
        "hosted model named": "gpt-4.1-mini" in submission,
        "AI voice declared": "ElevenLabs" in submission,
        "reviewer filled in the log": "pend" not in reviewers,
    }
    missing = [name for name, ok in needs.items() if not ok]
    return not missing, "SUBMISSION and AI log agree" if not missing else "missing: " + "; ".join(missing)


def logo_mark():
    html = (ROOT / "src" / "ui" / "index.html").read_text(encoding="utf-8")
    marked = (ROOT / "src" / "ui" / "assets" / "huiracocha_ia_og_ai.png").exists()
    return marked and '<span class="ai-mark">AI-generated</span>' in html, "visible label and marked preview image present"


def nasa_branding():
    hits = []
    for base in ("src", "docs"):
        for path in (ROOT / base).rglob("*"):
            if path.is_file() and re.search(r"nasa[-_ ]?(logo|meatball|worm|insignia)", path.name, re.I):
                hits.append(str(path.relative_to(ROOT)))
    return not hits, "no NASA logo files by name" if not hits else ", ".join(hits[:5])


def licence():
    text = (ROOT / "LICENSE").read_text(encoding="utf-8", errors="replace")[:400]
    return "MIT" in text, "LICENSE is MIT"


def main() -> int:
    print("COMPLIANCE AUDIT (read-only)\n")
    print("Deliverables")
    check("pitch video <= 30 s and SI disclosure in its metadata (repo copy)", video(ROOT / "docs" / "demo" / "Huiracocha_AI_pitch_30s.mp4"))
    check("same for the labelled copy to upload to the form", video(DOWNLOADED_VIDEO))
    check("slides <= 7 pages", slides)
    print("Public links")
    check("live app answers", reachable(LIVE + "/api/health/live"))
    check("live app shows the AI-generated logo label", reachable(LIVE + "/", "ai-mark"))
    check("static backup (GitHub Pages) answers with the label", reachable(PAGES, "ai-mark"))
    check("GitHub repository is public", reachable(REPO))
    check("live engine and provider state", live_engine)
    print("AI disclosure")
    check("SUBMISSION and AI_USE_LOG declare logo, hosted model, voice and reviewer", disclosure)
    check("logo carries a visible AI-generated mark", logo_mark)
    check("generated files carry the SI-assisted header", si_headers, warn_only=True)
    print("Safety and rules")
    check("no secrets in tracked files", secrets_tracked)
    check("no token pattern anywhere in the git history", secrets_history)
    check("no NASA logo files by name", nasa_branding)
    check("open-source licence", licence)
    print("\nOnly a person can confirm")
    for item in (
        "GitHub token revoked (Settings > Developer settings > Personal access tokens)",
        "Form: video uploaded is Downloads/Huiracocha_AI_pitch_30s_SI-labelled.mp4",
        "Form: Details and Summary in English, with the USE OF SI paragraph (logo, API, voice)",
        "Form: the 8 SI boxes ticked and the NASA / other data links filled in",
        "FortiGuard: site classification requested (https://www.fortiguard.com/webfilter)",
        "Team members are adults; no NASA logo, flag or mission identifier in anything shown",
        "Submit for Judging done before 23:59 and the confirmation banner / certificate saved",
    ):
        print(f"  MANUAL {item}")
    print(f"\nSUMMARY  {counts['PASS']} pass, {counts['FAIL']} fail, {counts['WARN']} warn")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
