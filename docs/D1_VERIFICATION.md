# D1 seal verification record — Colima

**Run ID:** `seal-20261107-d1`

**Date:** 2026-11-07

**Topology:** macOS M2 Pro / Colima docker runtime; no experiment agent process started.

**Result:** **PASS after fail-closed remediation.** Raw evidence remains gitignored and was not committed.

## Automated positive gate

`RUN_ID=seal-20261107-d1 CANARY_INTERVAL=5 lab/bin/up.sh` completed successfully. Both the byte-identical
agent sandbox and the model-proxy reported `passed:true` for:

- raw public IPv4 (`1.1.1.1:443`, `8.8.8.8:53`) and IPv6 (`2606:4700:4700::1111`) denial;
- explicit IPv6-disabled state, metadata, link-local, loopback, and lab-gateway controls;
- expected opaque mock A records, authoritative NXDOMAIN for real API names and fresh per-run nonce names;
- authenticated flat-depot positive control, fixed local model health, and rejection of non-completion/
  query-selected proxy routes;
- direct origin/hub denial from the agent;
- the proxy's sole host-gateway:11434 exception (connection refused was accepted because ollama is not
  required for D1).

Repeated periodic agent+proxy checks passed. The runtime topology checker accepted a one-network canary and
rejected the same canary after a second **internal** test network was attached; this test opened no external
route.

## Kill-switch and telemetry gate

The synthetic anomaly went through the production monitor action. Both canary and proxy reached
`State.Status=paused` / `State.Paused=true`; heartbeat records did not advance during two seconds frozen,
pre-freeze records remained intact, and heartbeat resumed only after explicit unpause. Telemetry services
were not paused.

Non-empty evidence was confirmed for all layers: `app/`, `proxy/model-io.jsonl`, `services/*.jsonl`,
`network/labnet.pcap`, and `network/nftables-drops.jsonl`. Drop records included real gateway-reject packets
on `hf-labnet` inside the Colima VM.

## Negative/fail-closed evidence

- Stopping depot made the positive control time out, both verification roles fail, the gate exit nonzero,
  and the proxy freeze. The depot was restored and a full positive gate rerun passed.
- Earlier starts correctly failed on telemetry `/dev/kmsg` permissions, gateway reachability, and direct
  target access from a stale target firewall. No agent was started; fixes were followed by a clean gate.
- Sixteen unit tests cover route/policy denial, timeout-inconclusive behavior, successful-connection
  failure, IPv6-disabled handling, NXDOMAIN specificity, flat positive controls, and proxy allowlisting.
  Compose validation, shellcheck, sensitive-file checks, and whitespace checks pass.

## Scope and caveats

D1 does not claim a model smoke test, behavioral result, independent red-team-subagent review, or a clean
zero-hole air-gap. The local dual-homed proxy is **one controlled, verified, strictly-weaker hole** to host
ollama. The funded GPU VM must validate the stronger in-lab-model/zero-hole topology. D2–D5 remain pending;
all scored runs follow the frozen `PRE-REGISTRATION.md`.
