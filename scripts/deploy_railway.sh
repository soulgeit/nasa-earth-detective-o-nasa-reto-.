#!/usr/bin/env bash
# SI-assisted: cfable (Claude Sonnet 5.5)
# Deploy the LIGHT image (verified rules + RAG, no torch) to the production Railway service.
#
#   bash scripts/deploy_railway.sh            pre-flight checks only; changes nothing
#   bash scripts/deploy_railway.sh --deploy   checks, uploads, deploys, then verifies the live URL
#
# Why the light image: on 2026-11-15 17:31 the heavy one (torch + SmolLM2 loaded inside the
# first chat request) left the public URL hanging for everybody. This image answers in
# milliseconds and has served every smoke test since the first deployment.
#
# `railway up` uploads the WORKING TREE, so a deploy refuses to run on uncommitted files
# unless --allow-dirty is given.
set -euo pipefail

PROJECT="802f90ea-4480-47bd-bd90-af34913087af"
ENVIRONMENT="production"
# The CLI cannot resolve this service by name (it ends in a hyphen): use its id.
SERVICE="669481f5-a577-4518-898a-84cc6ebf1635"
URL="https://huiracochaia.soulgeit.com"

DEPLOY=0
ALLOW_DIRTY=0
SKIP_TESTS=0
for arg in "$@"; do
  case "$arg" in
    --deploy) DEPLOY=1 ;;
    --allow-dirty) ALLOW_DIRTY=1 ;;
    --skip-tests) SKIP_TESTS=1 ;;  # only when this exact code already passed the suite
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

cd "$(dirname "${BASH_SOURCE[0]}")/.."
say() { printf '\n[%s] %s\n' "$1" "$2"; }

say "1/6" "the image must be the light one (no torch, rules + RAG)"
grep -q '^FROM python:3.12-slim' Dockerfile
grep -q 'AI_MODE=extractive' Dockerfile
if grep -vE '^[[:space:]]*#' Dockerfile | grep -qiE 'torch|transformers|peft'; then
  echo "Dockerfile pulls the ML stack: that is the image that hung production. Use Dockerfile.lora only on a machine with a GPU." >&2
  exit 1
fi
grep -q 'COPY data/knowledge/' Dockerfile

say "2/6" "knowledge fragments pass the strict gate"
python scripts/validate_fragments.py

say "3/6" "full test suite"
if [[ "$SKIP_TESTS" -eq 1 ]]; then
  echo "skipped (--skip-tests): the same code already passed"
else
  python -m pytest -q -p no:cacheprovider
fi

say "4/6" "working tree"
if [[ -n "$(git status --porcelain)" ]]; then
  git status --short | head -15
  if [[ "$ALLOW_DIRTY" -ne 1 && "$DEPLOY" -eq 1 ]]; then
    echo "uncommitted files would be uploaded: commit first (or pass --allow-dirty)." >&2
    exit 1
  fi
fi
echo "commit: $(git rev-parse --short HEAD) on $(git rev-parse --abbrev-ref HEAD)"

if [[ "$DEPLOY" -ne 1 ]]; then
  echo
  echo "Pre-flight passed. Nothing was deployed. To deploy: bash scripts/deploy_railway.sh --deploy"
  exit 0
fi

say "5/6" "railway up (service $SERVICE, environment $ENVIRONMENT)"
railway whoami
railway up --detach --project "$PROJECT" --environment "$ENVIRONMENT" --service "$SERVICE"

say "6/6" "waiting for $URL to answer, then verifying"
for i in $(seq 1 60); do
  if curl -fsS -m 8 "$URL/api/health/live" >/dev/null 2>&1; then break; fi
  printf '.'
  sleep 10
done
echo
curl -fsS -m 15 "$URL/api/health" | python -c "import json,sys; h=json.load(sys.stdin); print('health:', h['status'], '| ai_mode:', h['ai_mode'])"
for n in 1 2; do
  curl -fsS -m 20 "$URL/api/ai/about?lang=en" -o /dev/null -w "about call $n: %{http_code}\n"
done
curl -fsS -m 30 -X POST "$URL/api/ai/chat" -H 'content-type: application/json' \
  -d '{"message":"hola","lang":"es"}' | python -c "import json,sys; r=json.load(sys.stdin); assert r['kind']=='greeting', r; print('chat: greeting OK')"
python scripts/smoke_api.py "$URL"

cat <<EOF

Deployed. If something is wrong, roll back by deploying the last known-good commit
(main@b4a45b7, the light image) from a clean worktree:
  git worktree add ../etd-rollback b4a45b7 && cd ../etd-rollback \\
    && railway up --detach --project $PROJECT --environment $ENVIRONMENT --service $SERVICE
EOF
