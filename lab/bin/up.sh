#!/bin/sh
set -eu
# shellcheck source=/dev/null
. "$(dirname "$0")/common.sh"
printf '%s\n' "$RUN_ID" > "$ROOT_DIR/run/current-run"
# Never pull or start an agent implicitly during SEAL.
docker compose up -d --no-build --pull never --wait --wait-timeout 90 dns depot origin hub model-proxy telemetry
"$LAB_DIR/bin/verify-seal.sh" --with-kill-test
if [ -f "$ROOT_DIR/run/canary.pid" ] && kill -0 "$(cat "$ROOT_DIR/run/canary.pid")" 2>/dev/null; then
  kill "$(cat "$ROOT_DIR/run/canary.pid")" || true
fi
nohup "$LAB_DIR/bin/periodic-canary.sh" > "$TELEMETRY_DIR/control/periodic-canary.log" 2>&1 &
printf '%s\n' "$!" > "$ROOT_DIR/run/canary.pid"
printf 'SEAL VERIFIED for %s. No experiment agents started. Periodic canary PID %s.\n' "$RUN_ID" "$!"
