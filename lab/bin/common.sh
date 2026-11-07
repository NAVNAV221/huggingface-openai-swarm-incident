#!/bin/sh
# shellcheck shell=sh
LAB_DIR="$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)"
ROOT_DIR="$(CDPATH='' cd -- "$LAB_DIR/.." && pwd)"
export COMPOSE_FILE="$LAB_DIR/compose.yaml"
export COMPOSE_PROJECT_NAME=hf-swarm-lab
if [ -z "${RUN_ID:-}" ] && [ -f "$ROOT_DIR/run/current-run" ]; then
  RUN_ID="$(cat "$ROOT_DIR/run/current-run")"
fi
RUN_ID="${RUN_ID:-seal-dev}"
case "$RUN_ID" in
  *[!A-Za-z0-9._-]*|"") echo "invalid RUN_ID" >&2; exit 2 ;;
esac
export RUN_ID
TELEMETRY_DIR="$ROOT_DIR/telemetry/runs/$RUN_ID"
mkdir -p "$TELEMETRY_DIR/app" "$TELEMETRY_DIR/proxy" "$TELEMETRY_DIR/services" "$TELEMETRY_DIR/network" "$TELEMETRY_DIR/seal" "$TELEMETRY_DIR/control" "$ROOT_DIR/run"
