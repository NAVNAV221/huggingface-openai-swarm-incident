#!/bin/sh
set -eu
# shellcheck source=/dev/null
. "$(dirname "$0")/common.sh"
REASON=manual
if [ "${1:-}" = "--reason" ]; then
  REASON="${2:?missing reason}"
fi
# Docker IDs are safe, whitespace-delimited positional values.
# shellcheck disable=SC2046
set -- $(docker ps -q --filter label=lab.project=hf-swarm --filter label=lab.role=agent)
AGENTS="$*"
# shellcheck disable=SC2046
set -- $(docker ps -q --filter label=lab.project=hf-swarm --filter label=lab.role=model-proxy)
PROXIES="$*"
# shellcheck disable=SC2086
set -- $AGENTS $PROXIES
python3 - "$TELEMETRY_DIR/control/kill-switch.jsonl" "$RUN_ID" "$REASON" "$AGENTS" "$PROXIES" <<'PY'
import json, os, sys, time
path, run_id, reason, agents, proxies = sys.argv[1:]
with open(path, "a", encoding="utf-8") as stream:
    stream.write(json.dumps({"run_id":run_id,"ts":time.time(),"reason":reason,"agents":agents.split(),"proxies":proxies.split(),"event":"freeze_requested"},separators=(",",":"))+"\n")
    stream.flush(); os.fsync(stream.fileno())
PY
if [ "$#" -gt 0 ]; then
  # cgroup freezer is uncatchable by agent code; telemetry/mock services are excluded.
  docker pause "$@"
fi
printf 'FROZEN: agents=[%s] proxy=[%s] reason=%s\n' "$AGENTS" "$PROXIES" "$REASON"
