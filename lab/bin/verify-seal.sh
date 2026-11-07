#!/bin/sh
set -u
# shellcheck source=/dev/null
. "$(dirname "$0")/common.sh"
FAILED=0
python3 "$LAB_DIR/bin/check-agent-topology.py" || FAILED=1
if [ "$FAILED" -ne 0 ]; then
  "$LAB_DIR/bin/kill-switch.sh" --reason agent-topology-failed || true
  exit 1
fi
printf 'Verifying byte-identical agent sandbox (run %s)...\n' "$RUN_ID"
docker compose run --rm --no-deps agent-verifier || FAILED=1
printf 'Re-verifying model-proxy namespace...\n'
docker compose exec -T model-proxy python /opt/lab/seal_verify.py --role proxy || FAILED=1
python3 "$LAB_DIR/bin/check-agent-topology.py" || FAILED=1
if [ "$FAILED" -ne 0 ]; then
  "$LAB_DIR/bin/kill-switch.sh" --reason seal-verification-failed || true
  echo "SEAL VERIFICATION FAILED: run is frozen and must not start" >&2
  exit 1
fi
if [ "${1:-}" = "--with-kill-test" ]; then
  "$LAB_DIR/bin/kill-switch-test.sh" || FAILED=1
fi
if [ "$FAILED" -ne 0 ]; then
  echo "KILL-SWITCH VERIFICATION FAILED: run must not start" >&2
  exit 1
fi
printf 'SEAL VERIFIED: %s\n' "$RUN_ID"
