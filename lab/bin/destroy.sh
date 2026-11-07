#!/bin/sh
set -eu
# shellcheck source=/dev/null
. "$(dirname "$0")/common.sh"
YES=0
KEEP_RAW=0
for arg in "$@"; do
  case "$arg" in --yes) YES=1;; --retain-raw) KEEP_RAW=1;; *) echo "usage: destroy.sh --yes [--retain-raw]" >&2; exit 2;; esac
done
[ "$YES" -eq 1 ] || { echo "refusing DESTROY without --yes" >&2; exit 2; }
if [ -f "$ROOT_DIR/run/canary.pid" ]; then
  kill "$(cat "$ROOT_DIR/run/canary.pid")" 2>/dev/null || true
  rm -f "$ROOT_DIR/run/canary.pid"
fi
# Remove all ephemeral verification/kill canaries before destroying the core.
IDS="$(docker ps -aq --filter label=lab.project=hf-swarm --filter label=lab.ephemeral)"
# shellcheck disable=SC2086
[ -z "$IDS" ] || docker rm -f $IDS >/dev/null
# Explicitly remove the VM host-netns drop table even if the sidecar died unexpectedly.
docker compose exec -T telemetry nft delete table inet hf_lab 2>/dev/null || true
docker compose down --volumes --remove-orphans
if [ "$KEEP_RAW" -eq 0 ]; then
  case "$TELEMETRY_DIR" in "$ROOT_DIR"/telemetry/runs/*) rm -rf "$TELEMETRY_DIR";; *) exit 2;; esac
  echo "Raw telemetry destroyed; only separately exported sanitized artifacts may remain."
else
  echo "WARNING: retained UNSANITIZED raw telemetry at $TELEMETRY_DIR (gitignored)." >&2
fi
rm -f "$ROOT_DIR/run/current-run"
printf 'DESTROY complete for %s: containers, networks, and mock volumes removed.\n' "$RUN_ID"
