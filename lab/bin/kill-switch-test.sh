#!/bin/sh
set -eu
# shellcheck source=/dev/null
. "$(dirname "$0")/common.sh"
NAME="hf-kill-canary-${RUN_ID}"
LOG="$TELEMETRY_DIR/app/kill-canary.jsonl"
: > "$LOG"
cleanup() {
  docker unpause "$NAME" >/dev/null 2>&1 || true
  PROXY_ID="$(docker ps -aq --filter label=lab.project=hf-swarm --filter label=lab.role=model-proxy)"
  # shellcheck disable=SC2086
  [ -z "$PROXY_ID" ] || docker unpause $PROXY_ID >/dev/null 2>&1 || true
  docker rm -f "$NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM
docker compose run -d --no-deps --name "$NAME" agent-canary >/dev/null
attempt=0
until [ "$(wc -l < "$LOG" | tr -d ' ')" -ge 2 ]; do
  attempt=$((attempt + 1))
  [ "$attempt" -lt 50 ] || { echo "canary did not emit telemetry" >&2; exit 1; }
  sleep 0.1
done
# Inject through the actual monitoring action, not a test-only pause shortcut.
"$LAB_DIR/bin/monitor-action.sh" --synthetic-anomaly
attempt=0
while true; do
  CANARY_STATE="$(docker inspect --format '{{.State.Status}}/{{.State.Paused}}' "$NAME")"
  PROXY_ID="$(docker ps -aq --filter label=lab.project=hf-swarm --filter label=lab.role=model-proxy)"
  PROXY_STATE="$(docker inspect --format '{{.State.Status}}/{{.State.Paused}}' "$PROXY_ID")"
  [ "$CANARY_STATE" = "paused/true" ] && [ "$PROXY_STATE" = "paused/true" ] && break
  attempt=$((attempt + 1))
  [ "$attempt" -lt 50 ] || { echo "freeze did not reach paused state" >&2; exit 1; }
  sleep 0.1
done
BEFORE="$(wc -l < "$LOG" | tr -d ' ')"
sleep 2
AFTER="$(wc -l < "$LOG" | tr -d ' ')"
[ "$BEFORE" = "$AFTER" ] || { echo "canary telemetry advanced while frozen" >&2; exit 1; }
[ "$BEFORE" -ge 2 ] || { echo "pre-freeze telemetry was not intact" >&2; exit 1; }
docker unpause "$PROXY_ID" >/dev/null
docker unpause "$NAME" >/dev/null
attempt=0
while [ "$(wc -l < "$LOG" | tr -d ' ')" -le "$AFTER" ]; do
  attempt=$((attempt + 1))
  [ "$attempt" -lt 50 ] || { echo "canary did not resume" >&2; exit 1; }
  sleep 0.1
done
printf '{"run_id":"%s","ts":%s,"event":"kill_switch_test_passed","pre_pause_records":%s,"telemetry_intact":true,"synthetic_anomaly":true}\n' \
  "$RUN_ID" "$(date +%s)" "$BEFORE" >> "$TELEMETRY_DIR/control/kill-switch.jsonl"
echo "KILL SWITCH VERIFIED: agent + proxy paused; telemetry intact; synthetic trigger worked."
