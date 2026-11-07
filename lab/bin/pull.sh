#!/bin/sh
# PULL is the only intentional image-egress phase. No agent is started here.
set -eu
# shellcheck source=/dev/null
. "$(dirname "$0")/common.sh"
printf '%s\n' "$RUN_ID" > "$ROOT_DIR/run/current-run"
docker compose build --pull dns depot origin hub model-proxy telemetry agent-verifier
docker image inspect hf-swarm-sandbox:local hf-swarm-mocks:local hf-swarm-model-proxy:local hf-swarm-telemetry:local \
  --format '{{index .RepoDigests}} {{.Id}}' > "$TELEMETRY_DIR/control/image-digests.txt"
printf 'PULL complete for %s; run lab/bin/up.sh to SEAL+VERIFY.\n' "$RUN_ID"
