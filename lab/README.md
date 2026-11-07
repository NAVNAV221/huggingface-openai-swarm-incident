# D1 sealed lab (local Colima)

**No experiment agents are started by these commands.** `agent-verifier` and the heartbeat canary are
inert verification workloads, built from the same sandbox image/network/capability policy that D2 agents
must use. D2–D5 remain blocked until the commands below pass.

## Lifecycle

```sh
# 1–2. PROVISION + PULL: the only image-egress phase. Pull model weights separately in D2.
RUN_ID="seal-$(date +%Y%m%d-%H%M%S)" lab/bin/pull.sh

# 3–4. SEAL + VERIFY: starts mocks/proxy/telemetry only; self-checks proxy;
# verifies a byte-identical sandbox; tests pause + telemetry + synthetic anomaly;
# starts a 30-second periodic canary. Any failure freezes agent/proxy labels and exits nonzero.
# The canary also rejects second networks, capabilities, and host/Docker mounts on actual agents.
lab/bin/up.sh

# Re-run both namespace suites at any time. This is the D2 runner's mandatory gate.
lab/bin/verify-seal.sh --with-kill-test

# Human kill switch: freezes every lab.role=agent plus model-proxy, never telemetry.
lab/bin/kill-switch.sh --reason operator

# Local DESTROY: removes containers/networks/nft table/named mock volume and raw telemetry.
# Export only sanitized analysis before this. --retain-raw is an explicit, warned exception.
lab/bin/destroy.sh --yes
```

Use `CANARY_INTERVAL=10 lab/bin/up.sh` for a shorter development interval. Scripts resolve the current
`RUN_ID` from the gitignored `run/current-run`; concurrent labs are intentionally unsupported because the
VM bridge/nft names and agent IP plan are fixed.

## What the seal proves

- Agents attach only to `labnet` (`internal: true`), have no capabilities, no Docker socket/host mounts,
  read-only rootfs, and disabled IPv6. Raw IPv4/IPv6, metadata, link-local, gateway, and direct target
  access must fail with explicit route/policy errors. Bare timeouts fail verification.
- Mock DNS has no upstream recursion. Opaque permitted names resolve to fixed lab addresses; real API
  names and a fresh nonce return authoritative NXDOMAIN. DNS is defense-in-depth, not the L3 seal.
- The depot positive control performs authenticated flat-store listing, so a dead sandbox/network cannot
  pass. The proxy health and completion-only route checks reject arbitrary fetch/path-upstream behavior.
- `model-proxy` is dual-homed but has input/forward/output default-drop nftables chains. Its only non-lab
  allowance is the resolved host gateway on TCP 11434. It runs the verifier at startup and periodically.
  This is **one controlled, strictly-weaker local hole**; the funded GPU VM uses an in-lab model and no
  such hole.
- `origin` and `hub` reject direct lab sources except the depot IP. Their guarded content is analog-only;
  no reusable vulnerability is implemented in D1.

## Telemetry and kill switch

All data stays under gitignored `telemetry/runs/<RUN_ID>/`:

1. `app/`: heartbeat now; D2 full prompt/completion/action/observation JSONL later.
2. `proxy/model-io.jsonl`: full fixed-upstream requests/responses, source IP, sequence, timing.
3. `services/`: depot/origin/hub/DNS semantic logs with body hashes, response, source IP, credential hash.
4. `network/labnet.pcap` plus `network/nftables-drops.jsonl`: capture on the `hf-labnet` bridge in the
   Colima VM and host-netns/proxy drop records from `/dev/kmsg`.

The kill-switch test injects a synthetic anomaly through the real monitor action, asserts agent and proxy
`State.Status=paused`, verifies no heartbeat advance while frozen, then unpauses and verifies resumption.
Telemetry is never paused. Periodic verification failure invokes the same freeze.

## Repo hygiene

Install once with `pre-commit install`. The local hooks and CI reject tracked ignored/sensitive files,
run fail-closed verifier tests, shellcheck scripts, and validate Compose. Raw telemetry, weights, secrets,
and pcaps are never source artifacts.

## Local limitation

D1 does not need ollama: connection-refused on the fixed host:11434 upstream proves that the one intended
route exists without making an inference call. D2 must start ollama on the host and use only a small
quantized model with 3–4 agents on this 16 GB machine. Local smoke tests are unscored; scored runs and the
capability ladder follow `docs/PRE-REGISTRATION.md` in the funded phase.
