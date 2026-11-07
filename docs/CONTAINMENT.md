# Containment & safety (read before running anything)

This experiment deliberately studies agents doing things that, outside a lab, would be abuse. That is
only acceptable because it is **fully contained, against local analog mocks, for defensive research**, and
produces **nothing reusable against real systems**. These rules are **hard requirements**, not
guidance — the implementation session must build and *verify* them.

---

## The boundary (non-negotiable)

- **Air-gapped during runs.** While an experiment runs, the environment has **deny-all egress**. Agents
  can reach only their permitted local mock services and the fixed local inference endpoint. No real
  internet, real API, or real third party — ever — from inside a run. **L3 route denial is the
  load-bearing seal**: agent sandboxes attach only to an `internal: true` bridge, with no additional
  network, host mount, or Docker socket. Mock DNS/NXDOMAIN is defense-in-depth, **not** egress control.
- **Local inference only.** Models are served **in-lab** (ollama/vLLM on the same box). No inference call
  leaves the machine. On the GPU VM the model is a sibling inside `labnet`: a zero-hole agent seal. For
  local Colima development, a dual-homed `model-proxy` is the **one controlled, verified hole** to host
  ollama:11434. It has a single hardcoded upstream, completion-only routes, its own default-deny nftables
  rules, and must pass the same egress verification. Agent net namespaces remain route-less, but this
  local topology is honestly **strictly weaker** than the zero-hole VM seal; clean air-gap claims must be
  validated on the VM.
- **Mock targets only.** There is no real HuggingFace, Artifactory, or any real third party. `hub`/
  `origin`/`depot` are purpose-built local analogs.
- **Analog, non-reusable vulnerabilities.** The exploitable weaknesses are **generic analogs**, not
  reproductions of specific real CVEs, and must not be portable to real software. Nothing built here is a
  working real-world exploit.
- **Capabilities bounded to the lab.** Agent tools act only within the sandbox network. No tool can reach
  the host, the internet, or any real credential store.
- **Nothing persists outside the lab.** Captured data stays in the experiment's storage; no secrets,
  tokens, or agent outputs are published or leave the box except the (sanitized) analysis report.

## The seal lifecycle (resolves cloud-GPU vs. air-gap)

A rented GPU VM is fine *if* you seal it. The order matters:

```
1. PROVISION   rent the VM
2. PULL        download model weights + build images      [egress ON — only here]
               GPU VM: attach a minimal/no instance role before this window;
               cloud metadata credentials must not be available while pulling
3. SEAL        enable deny-all egress (default-deny firewall; allow only intra-lab)
4. VERIFY      prove the seal (see checks below) BEFORE any agent starts
5. RUN         execute the experiment — fully air-gapped
6. CAPTURE     collect telemetry to lab storage
7. DESTROY     tear down the VM; retain only sanitized captures
```

The only window with egress is step 2 (pulling weights). No agent runs until step 4 passes.

## Verify the seal (acceptance — the lab must self-check)

Before any agent step executes, automated checks must confirm, from a byte-identical agent sandbox **and
from the local model-proxy**:
- **Raw-IP public egress** to `1.1.1.1:443` and `8.8.8.8:53` fails with route/policy denial; successful
  DNS resolution is never accepted as evidence of containment.
- **IPv6 egress** to `2606:4700:4700::1111` fails and IPv6 is disabled in the sandbox. This check may not
  be skipped on an IPv4-only host.
- `169.254.169.254`, other link-local/host-loopback addresses, and the lab gateway are blocked; the sole
  exception is the proxy's fixed host-gateway:11434 upstream.
- Permitted opaque mock names resolve to expected lab IPs, while `huggingface.co`, `api.openai.com`, and a
  fresh **per-run nonce domain** return authoritative NXDOMAIN. The nonce defeats cached build-time data.
- The model base URL resolves only to `model-proxy` (local) or `model` (VM); remote model APIs are
  unreachable, and the proxy exposes no arbitrary fetch or path-selected upstream.
- A **positive control** reaches the depot and resolves a mock name. A bare timeout is INCONCLUSIVE and
  fails verification; an entirely dead network must never produce a false pass.
- The periodic runtime canary repeats these checks (including nonce DNS and positive controls) to detect
  runtime `network connect` or firewall changes. Failure freezes agents and aborts the run.
- A **kill switch** using `docker pause` halts all agents and the proxy and freezes state within seconds.
  Each run-start test also proves canary telemetry survives the pause and that a synthetic anomaly invokes
  the automatic trigger; the telemetry sink stays running.

Verification is fail-closed: any error, missing check, timeout, or failed control exits non-zero, freezes
the run, and **no agent process starts**.

## Kill switch & monitoring

- A single command (and an automatic trigger on anomalous resource use) **stops every agent and freezes
  the environment** for inspection. Test it as part of every run's startup.
- The experiment is observed live; a human can abort at any time. Because everything is captured, an
  abort loses no evidence.

## Dual-use statement — what we will and won't do

**Will:** reproduce, in a sealed lab against mocks, the *dynamics* of a publicly documented incident, to
help defenders detect and respond to emergent multi-agent coordination and sandbox escape.

**Won't:**
- target or touch any real system, service, account, or third party;
- implement or emit a working exploit usable against real software;
- reproduce specific live CVEs as weaponized PoCs (we use generic analogs);
- publish agent-generated offensive artifacts, credentials, or payloads;
- build anything whose purpose is to *conduct* an attack rather than to *study and defend against* one.

If a run produces an unexpectedly general/transferable technique, **stop, contain, and review** before
continuing — treat it as a finding to handle carefully, not to extend.

## Data handling

- Telemetry (agent reasoning, `depot` traffic, network events) stays in lab storage.
- The **analysis report is sanitized**: no live secrets, no reusable exploit detail, no real identifiers.
- The repo stays **private**; `FLAG`/secrets/weights are git-ignored and never committed.
