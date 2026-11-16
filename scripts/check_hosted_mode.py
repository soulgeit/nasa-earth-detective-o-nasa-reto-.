# SI-assisted: cfable (Claude Sonnet 5.5)
"""Prove the hosted-model mode end to end with a FAKE provider: no real key, no cost, no network.

    python scripts/check_hosted_mode.py

It starts a tiny OpenAI-compatible server (port 8765) and the real app (port 8099) with AI_MODE=full and
a fake key, then checks that:
  1. before any call the panel says "configured" and the engine is still rules+rag (nothing is advertised
     that has not worked);
  2. a question is planned by the provider, which received the bearer key, and the plan is labelled "llm";
  3. the panel then says llm+rag, and the key appears in no response and in no server log;
  4. a burst of chats against a SLOW provider never stalls the liveness probe, and the provider sees only a
     handful of the calls (the rest are answered by the verified rules at once);
  5. when the provider disappears the chat still answers (rules, with the reason) and the panel stops
     advertising it.
Exit code 0 only when every check passed.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_live import call  # noqa: E402

KEY = "sk-fake-e2e-0123456789abcdef"
PROVIDER_PORT, APP_PORT = 8765, 8099
APP = f"http://127.0.0.1:{APP_PORT}"


class Provider(BaseHTTPRequestHandler):
    delay = 0.0
    seen: list[str] = []

    def log_message(self, *args):  # silence
        pass

    def _send(self, status: int, body: dict) -> None:
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))) or b"{}")
        auth = self.headers.get("Authorization", "")
        Provider.seen.append(auth)
        if auth != f"Bearer {KEY}":
            return self._send(401, {"error": {"message": "Incorrect API key provided"}})
        time.sleep(Provider.delay)
        user = body["messages"][-1]["content"]
        if not user.startswith("QUESTION:"):  # an explanation request: give the guard something to reject
            return self._send(200, {"choices": [{"message": {"content": "The trend is 42.7 per decade [1]."}}]})
        question = user.split("\n", 1)[0][len("QUESTION:"):].strip()
        after = user.split("CANDIDATES:", 1)[1]
        ids = re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", after)
        variable = "PRECTOTCORR" if re.search(r"llue|lluvia|rain", question, re.I) and "PRECTOTCORR" in ids else (ids[0] if ids else "T2M")
        place = (re.findall(r"([A-ZÁÉÍÓÚÑ][\wáéíóúñ]+)\W*$", question) or ["Ica"])[0]
        plan = {"intent": "investigate", "variable_ids": [variable], "place": place, "place_b": None,
                "start_year": None, "end_year": None, "last_n_years": None, "hypothesis": "down", "lang": "es"}
        self._send(200, {"choices": [{"message": {"content": json.dumps(plan)}}]})


def main() -> int:
    failures: list[str] = []

    def check(ok: bool, label: str, detail: str = "") -> None:
        print(("  ok   " if ok else "  FAIL ") + label + (f"  [{detail}]" if detail else ""))
        if not ok:
            failures.append(label)

    provider = ThreadingHTTPServer(("127.0.0.1", PROVIDER_PORT), Provider)
    threading.Thread(target=provider.serve_forever, daemon=True).start()
    log = tempfile.NamedTemporaryFile("w+", suffix=".log", delete=False)
    env = dict(os.environ, AI_MODE="full", LLM_BASE_URL=f"http://127.0.0.1:{PROVIDER_PORT}/v1", LLM_API_KEY=KEY,
               PLANNER_MODEL="fake-small", EXPLAIN_MODEL="fake-small", EMBED_MODEL="")
    server = subprocess.Popen([sys.executable, "-m", "uvicorn", "src.api.main:app", "--port", str(APP_PORT), "--workers", "1"],
                              cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    bodies: list[str] = []
    try:
        for _ in range(90):
            if call(f"{APP}/api/health/live", timeout=2)[0] == 200:
                break
            time.sleep(1)
        else:
            print("the app never started; log:\n" + Path(log.name).read_text(errors="replace")[-1500:])
            return 2

        def get(path: str):
            status, payload, took = call(APP + path)
            bodies.append(json.dumps(payload))
            return status, payload, took

        def chat(message: str, **extra):
            status, payload, took = call(f"{APP}/api/ai/chat", data={"message": message, "lang": "es", **extra}, timeout=60)
            bodies.append(json.dumps(payload))
            return status, payload, took

        _, about, _ = get("/api/ai/about?lang=en")
        d = about["deployment"]
        check(d["llm"]["state"] == "configured" and d["engine"] == "rules+rag", "1. configured but not advertised before a real call",
              f"state={d['llm']['state']} engine={d['engine']}")

        status, reply, took = chat("¿Llueve menos en Ica?")
        plan = (reply or {}).get("plan") or {}
        check(status == 200 and plan.get("mode") == "llm" and plan.get("variable_ids") == ["PRECTOTCORR"],
              "2. the provider planned it and the plan is labelled llm", f"mode={plan.get('mode')} ids={plan.get('variable_ids')} in {took:.2f}s")
        check(Provider.seen and all(a == f"Bearer {KEY}" for a in Provider.seen), "2b. the provider received the bearer key", f"{len(Provider.seen)} call(s)")

        _, about, _ = get("/api/ai/about?lang=en")
        d = about["deployment"]
        check(d["engine"] == "llm+rag" and d["llm"]["state"] == "ready" and d["llm"]["host"] == "127.0.0.1",
              "3. after a real success the panel names the hosted model", f"engine={d['engine']} host={d['llm']['host']}")
        get("/api/health")

        # --- a slow provider and a burst of chats: the liveness probe must not stall
        Provider.delay = 1.5
        before = len(Provider.seen)
        pings: list[float] = []
        stop = threading.Event()

        def pinger():
            while not stop.is_set():
                status_, _, took_ = call(f"{APP}/api/health/live", timeout=10)
                pings.append(took_ if status_ == 200 else 99.0)
                time.sleep(0.1)

        results: list[tuple[int, str]] = []
        questions = ["¿Llueve menos en Ica?", "¿Hace más calor en Lima?", "heladas en Huancayo", "¿Qué está cambiando en Ayacucho?"] * 10

        def asker(text: str):
            status_, payload, _ = chat(text)
            results.append((status_, ((payload or {}).get("plan") or {}).get("mode", "-")))

        watcher = threading.Thread(target=pinger, daemon=True)
        watcher.start()
        threads = [threading.Thread(target=asker, args=(q,)) for q in questions]
        started = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=90)
        stop.set()
        watcher.join(timeout=5)
        worst = max(pings) if pings else 99.0
        reached = len(Provider.seen) - before
        check(len(results) == len(questions) and all(s == 200 for s, _ in results), "4. every chat of the burst was answered",
              f"{sum(1 for s, _ in results if s == 200)}/{len(questions)} in {time.time() - started:.1f}s")
        check(pings and worst < 1.0, "4b. the liveness probe never stalled during the burst", f"{len(pings)} pings, worst {worst:.2f}s")
        check(reached <= 16, "4c. the provider saw only a handful of the calls (the rest went to the rules)", f"{reached} of {len(questions)} reached it")
        Provider.delay = 0.0

        # --- the provider disappears
        provider.shutdown()
        provider.server_close()
        status, reply, took = chat("¿Hace más calor en Lima?")
        plan = (reply or {}).get("plan") or {}
        check(status == 200 and plan.get("mode") == "rules" and str(plan.get("note", "")).startswith("ai_unavailable"),
              "5. with the provider gone the chat still answers, by rules, saying why", f"mode={plan.get('mode')} note={str(plan.get('note'))[:48]} in {took:.2f}s")
        _, about, _ = get("/api/ai/about?lang=en")
        check(about["deployment"]["engine"] == "rules+rag" and about["deployment"]["llm"]["state"] == "failing",
              "5b. the panel stops advertising a failing provider", f"engine={about['deployment']['engine']} state={about['deployment']['llm']['state']}")

        leaked_in_bodies = any(KEY in b or KEY[:10] in b for b in bodies)
        check(not leaked_in_bodies, "6. the key appears in no response", f"{len(bodies)} responses scanned")
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
        log.flush()
        text = Path(log.name).read_text(errors="replace")
        check(KEY not in text and KEY[:10] not in text, "6b. the key appears in no server log", f"{len(text)} chars of log")
        try:
            os.unlink(log.name)
        except OSError:
            pass

    print("\nHOSTED MODE CHECK " + ("PASSED" if not failures else f"FAILED: {failures}"))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
