#!/bin/sh
set -eu
# shellcheck source=/dev/null
. "$(dirname "$0")/common.sh"
if [ "${1:-}" != "--synthetic-anomaly" ]; then
  echo "usage: monitor-action.sh --synthetic-anomaly" >&2
  exit 2
fi
# This is the same production action used for an anomaly; the test supplies a synthetic event.
exec "$LAB_DIR/bin/kill-switch.sh" --reason synthetic-anomaly
