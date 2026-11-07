# Build notes — START HERE (for the session that builds this)

Short orientation so you don't redo work. This is the **post-review** state; the design is reconciled and
ready to implement. Build happens in the worktree `build/sealed-lab` at
`/Users/navebennaim/Documents/Git/hf-swarm-incident-build` (off `master`).

## Read in this order
1. `docs/HANDOFF.md` — original task + binding protocol (worktree, concurrent SWE+PM review, /loop, checklist).
2. `docs/REVIEW_FINDINGS.md` — **the SWE + PM reviews are DONE; do not re-run them.** Findings + the
   reconciliation (§C) are the authority. §C1 = doc edits to make; §C2 = deliverables folded into D1–D5;
   §C3 = local-now vs funded-later split.
3. `docs/ARCHITECTURE.md` — the 3 diagrams (sealed-lab topology, phase/detector flow, seal lifecycle).
4. `docs/AGENT_CHECKLIST.md` — the gates (seal-verified-before-any-agent is a hard, in-code run gate).
5. `docs/CONTAINMENT.md` + `METHODOLOGY.md` + `EXPERIMENT.md` + `INFRA.md` — originals; some have known bugs
   the reconciliation fixes (see below).

## Decisions already made (do not re-litigate)
- **Backend: start LOCAL** (ollama + small open model on an M2 Pro, 16 GB). Local = air-gap-faithful
  (on-box inference), so the CONTAINMENT two-plane deviation is NOT needed locally.
- **16 GB is tight → local dev = 3–4 agents + a small quant.** Local ≠ full scale. The scored runs,
  capability ladder, and ~60-run power happen in the **funded phase** (OpenRouter/Crusoe) — OpenRouter there
  reintroduces an off-machine inference-egress deviation that needs explicit sign-off.
- The model ladder (Llama-3.1-8B/Qwen2.5-7B → 32B → 70B) is a documented capability variable, not a fix.

## Known doc bugs the build must fix (from reviews)
- **INFRA.md:13** `http://localhost/v1` is wrong on BOTH topologies → local `http://model-proxy:11434/v1`,
  VM `http://model:8000/v1`. A naive "allow the host" fix voids the seal.
- **Seal = L3 route denial** (`internal: true`) is load-bearing; **DNS→mocks is defense-in-depth, not egress
  control.** Verification needs **raw-IP egress + IPv6 + nonce-DNS + a positive control**, fail-closed, re-
  checked periodically (not just t0). (CONTAINMENT "Verify the seal" is missing these.)
- Agent-visible service names must be **opaque** (not hub/origin); errors generic; depot a flat store (no
  feed); no pre-seeded message; egress surface de-saliencied. (Science validity — PM §A.4.)

## What's built so far
- §C1 doc edits + frozen `docs/PRE-REGISTRATION.md` committed (`7c07565`).
- **D1 sealed lab implemented and proven on Colima** (`seal-20261107-d1`): internal labnet, opaque mock
  DNS/services, hardened self-verified model-proxy, fail-closed agent+proxy verification, periodic canary
  + runtime topology checks, pause/kill test, four-layer telemetry, hygiene hooks, DESTROY.
- Live positive gate and kill-switch pass; dead-depot negative gate freezes; second-network negative check
  fails. No experiment agents have run. `ollama` is not installed yet (needed for D2 smoke-test).

## Next action (where to start)
1. ~~Apply §C1 docs + pre-registration~~ **DONE** (`7c07565`).
2. ~~Build + prove D1 on Colima~~ **DONE**; see `lab/README.md` and `worklog.md` for the evidence.
3. **Next: D2 agents/ReAct**, only through the existing `lab/bin/verify-seal.sh --with-kill-test` gate. Then D3
   preconditions + prompt-audit, D4 runner+controls+telemetry, D5 analysis+replay.

## Containment flag to keep visible
Local model-proxy = **one controlled, verified egress hole** (agents → proxy → host ollama). It keeps
everything on-box but makes the local seal **strictly weaker** than the GPU-VM seal (model in-lab, zero
holes). State this honestly in any report; validate the clean air-gap claim on the VM.
