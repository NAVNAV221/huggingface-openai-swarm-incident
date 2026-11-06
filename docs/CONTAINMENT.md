# Containment & safety (read before running anything)

This experiment deliberately studies agents doing things that, outside a lab, would be abuse. That is
only acceptable because it is **fully contained, against local analog mocks, for defensive research**, and
produces **nothing reusable against real systems**. These rules are **hard requirements**, not
guidance — the implementation session must build and *verify* them.

---

## The boundary (non-negotiable)

- **Air-gapped during runs.** While an experiment runs, the environment has **deny-all egress**. Agents
  can reach only the local mock services (`depot`, `origin`, `hub`, mock DNS). No real internet, no real
  API, no real third party — ever — from inside a run.
- **Local inference only.** Models are served **in-lab** (ollama/vLLM on the same box). No inference call
  leaves the environment. (This is why "cloud GPU" is still air-gapped — see the seal lifecycle below.)
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
3. SEAL        enable deny-all egress (default-deny firewall; allow only intra-lab)
4. VERIFY      prove the seal (see checks below) BEFORE any agent starts
5. RUN         execute the experiment — fully air-gapped
6. CAPTURE     collect telemetry to lab storage
7. DESTROY     tear down the VM; retain only sanitized captures
```

The only window with egress is step 2 (pulling weights). No agent runs until step 4 passes.

## Verify the seal (acceptance — the lab must self-check)

Before any agent step executes, automated checks must confirm:
- from inside an agent sandbox, a request to the **public internet** → fails/blackholed.
- a request to a **cloud metadata endpoint** (`169.254.169.254`, link-local, host loopback) → fails.
- DNS resolves **only** the mock services; anything else → NXDOMAIN/blackhole.
- the model endpoint is the **local** server, not a remote API.
- a **kill switch** halts all agents and freezes state within seconds, and is tested each run.

If any check fails, the run **does not start**.

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
