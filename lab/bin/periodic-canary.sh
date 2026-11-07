#!/bin/sh
set -u
# shellcheck source=/dev/null
. "$(dirname "$0")/common.sh"
INTERVAL="${CANARY_INTERVAL:-30}"
case "$INTERVAL" in *[!0-9]*|"") echo "invalid CANARY_INTERVAL" >&2; exit 2;; esac
while true; do
  printf '{"run_id":"%s","ts":%s,"event":"periodic_verification_start"}\n' "$RUN_ID" "$(date +%s)"
  if ! "$LAB_DIR/bin/verify-seal.sh"; then
    echo "periodic seal failure; invoking freeze" >&2
    "$LAB_DIR/bin/kill-switch.sh" --reason periodic-seal-failure || true
    exit 1
  fi
  sleep "$INTERVAL"
done
