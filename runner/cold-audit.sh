#!/bin/sh
set -eu
ROOT_DIR="$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)"
LAB_DIR="$ROOT_DIR/lab"
export COMPOSE_FILE="$LAB_DIR/compose.yaml"
export COMPOSE_PROJECT_NAME=hf-swarm-lab
RUN_ID="${RUN_ID:-$(cat "$ROOT_DIR/run/current-run")}"
export RUN_ID
TELEMETRY_DIR="$ROOT_DIR/telemetry/runs/$RUN_ID"
"$LAB_DIR/bin/verify-seal.sh" >/dev/null
python3 "$ROOT_DIR/runner/prompt_audit.py" bundle > "$ROOT_DIR/run/prompt-audits/bundle-result.json"
mkdir -p "$TELEMETRY_DIR/audits"
cp "$ROOT_DIR/run/prompt-audits/bundle.json" "$TELEMETRY_DIR/audits/bundle.json"
docker compose run --rm --no-deps agent-verifier python /opt/lab/cold_audit.py
DIGEST="$(python3 -c 'import json; print(json.load(open("run/prompt-audits/bundle-result.json"))["bundle_sha256"])')"
cp "$TELEMETRY_DIR/audits/$DIGEST.json" "$ROOT_DIR/run/prompt-audits/$DIGEST.json"
python3 "$ROOT_DIR/runner/prompt_audit.py" verify
