# SI-assisted: cfable (Claude Sonnet 5.5)
"""Verify a deployed Huiracocha IA URL, including that the chat cannot hang the server.

    python scripts/verify_live.py https://huiracochaia.soulgeit.com [--wait 480]

1. waits until the NEW version answers (/api/ai/about exists only in it);
2. checks the mode (the public image must run verified rules + RAG);
3. greets, asks and compares through /api/ai/chat;
4. fires many chats in parallel while pinging /api/health/live, and fails if any ping is slow;
5. runs one all-variables scan.
Exit code 0 only when every check passed.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request


def call(url: str, *, data: dict | None = None, timeout: float = 60.0) -> tuple[int, dict | None, float]:
    body = json.dumps(data).encode() if data is not None else None
    request = urllib.request.Request(url, data=body, headers={"content-type": "application/json"} if body else {})
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8") or "null")
            return response.status, payload, time.time() - started
    except urllib.error.HTTPError as exc:
        return exc.code, None, time.time() - started
    except Exception:
        return 0, None, time.time() - started


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--wait", type=int, default=480, help="seconds to wait for the new version")
    parser.add_argument("--hosted", action="store_true",
                        help="the server runs with a hosted model (AI_MODE=full + LLM_API_KEY): different expectations")
    args = parser.parse_args()
    # A hosted plan answers in seconds, not milliseconds; everything else about the burst stays the same.
    slow = 8.0 if args.hosted else 3.0
    engines = ("rules+rag", "llm+rag") if args.hosted else ("rules+rag",)
    base = args.url.rstrip("/")
    failures: list[str] = []

    def check(ok: bool, label: str, detail: str = "") -> None:
        print(("  ok   " if ok else "  FAIL ") + label + (f"  [{detail}]" if detail else ""))
        if not ok:
            failures.append(label)

    print(f"waiting for the new version at {base} (up to {args.wait}s)")
    deadline = time.time() + args.wait
    while time.time() < deadline:
        status, _, _ = call(f"{base}/api/ai/about?lang=en", timeout=15)
        if status == 200:
            break
        time.sleep(8)
    else:
        print("the new version never answered")
        return 2

    status, health, took = call(f"{base}/api/health")
    expected_mode = "full" if args.hosted else "extractive"
    check(status == 200 and health and health.get("ai_mode") == expected_mode,
          "hosted model configured" if args.hosted else "public image runs verified rules + RAG",
          f"ai_mode={health and health.get('ai_mode')} in {took:.2f}s")

    for n in (1, 2, 3):
        status, about, took = call(f"{base}/api/ai/about?lang=es")
        check(status == 200 and about and about["deployment"]["engine"] in engines, f"about call {n}", f"{took:.2f}s")
    if about:
        corpus = about["corpus"]
        check(corpus["documents"] >= 990 and corpus["skipped_rows"] == 0, "corpus loaded without skipped rows",
              f"{corpus['documents']} documents")

    for message, lang, kind in (("hola", "es", "greeting"), ("hi", "en", "greeting"),
                                ("¿Llueve menos en Ica?", "es", "plan"), ("¿y en Huancayo?", "es", "plan")):
        ctx = {"place": "Ica", "variable_id": "PRECTOTCORR"} if message.startswith("¿y") else {}
        status, reply, took = call(f"{base}/api/ai/chat", data={"message": message, "lang": lang, "context": ctx})
        check(status == 200 and reply and reply["kind"] == kind and took < slow, f"chat {message!r}",
              f"{reply and reply['kind']} in {took:.2f}s")

    if args.hosted:
        # After real plan questions the panel must name the provider, and nothing may carry a key.
        status, about, _ = call(f"{base}/api/ai/about?lang=en")
        llm = (about or {}).get("deployment", {}).get("llm", {})
        check(status == 200 and llm.get("state") == "ready" and (about["deployment"]["engine"] == "llm+rag"),
              "the provider answered for real (panel says llm+rag)", f"state={llm.get('state')} host={llm.get('host')}")
        _, health_again, _ = call(f"{base}/api/health")
        check("sk-" not in json.dumps([about, health_again]), "no API key appears in the public responses")

    # --- the incident of 2026-11-15: a burst of chats must never block everybody else
    questions = ["hola", "¿Hace más calor en Lima?", "heladas en Huancayo", "Compara la lluvia de Andahuaylas y Lima",
                 "¿qué puedes hacer?", "viento en Ica", "¿qué es Mann-Kendall?", "Is the wind getting stronger in Ica?",
                 "radiación UV en Ayacucho", "¿qué variables tienes?", "gracias", "¿Qué está cambiando en Ayacucho?"] * 8
    pings: list[float] = []
    stop = threading.Event()

    def pinger() -> None:
        while not stop.is_set():
            status, _, took = call(f"{base}/api/health/live", timeout=10)
            pings.append(took if status == 200 else 99.0)
            time.sleep(0.25)

    results: list[tuple[int, float]] = []

    def asker(text: str) -> None:
        status, _, took = call(f"{base}/api/ai/chat", data={"message": text, "lang": "es"}, timeout=60)
        results.append((status, took))

    watcher = threading.Thread(target=pinger, daemon=True)
    watcher.start()
    workers = [threading.Thread(target=asker, args=(q,)) for q in questions]
    started = time.time()
    for w in workers:
        w.start()
    for w in workers:
        w.join(timeout=90)
    stop.set()
    watcher.join(timeout=5)
    elapsed = time.time() - started
    ok_count = sum(1 for status, _ in results if status == 200)
    slowest = max((t for _, t in results), default=0.0)
    check(ok_count == len(questions), f"{len(questions)} chats in parallel all answered",
          f"{ok_count}/{len(questions)}, slowest {slowest:.2f}s, total {elapsed:.2f}s")
    worst_ping = max(pings) if pings else 99.0
    # A single-process server queues a spike of ~100 simultaneous requests: a ping sent in the middle of
    # it waits for the spike (seconds). The incident of 2026-11-15 was different: nobody was answered for
    # minutes. So the checks are: no ping fails, none takes tens of seconds, and the server is back to
    # normal the moment the burst ends.
    check(pings and worst_ping < 10.0 and all(p < 99.0 for p in pings), "no health ping failed or stalled during the burst",
          f"{len(pings)} pings, worst {worst_ping:.2f}s" if pings else "no pings")
    status, _, after = call(f"{base}/api/health/live", timeout=10)
    check(status == 200 and after < 1.5, "the server is back to normal right after the burst", f"{after:.2f}s")

    status, scan, took = call(f"{base}/api/scan?lat=-12.0687&lon=-75.2103&place=Huancayo", timeout=120)
    check(status == 200 and scan and scan["n_tested"] >= 28, "all-variables scan (Huancayo)",
          f"{scan and scan['n_tested']} tested, {scan and scan['n_confirmed']} confirmed in {took:.1f}s")
    status, scan2, took2 = call(f"{base}/api/scan?lat=-12.0687&lon=-75.2103&place=Huancayo", timeout=60)
    check(status == 200 and took2 < 3.0, "the repeated scan comes from the cache", f"{took2:.2f}s")

    print("\nLIVE CHECK " + ("PASSED" if not failures else f"FAILED: {failures}"))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
