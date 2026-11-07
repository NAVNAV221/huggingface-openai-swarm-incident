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
- §C1 docs + frozen pre-registration (`82ff364`); D1 sealed lab (`9be0a0c`); D2 ReAct (`bfc3592`);
  D3 preconditions/audit (`4cf3618`); D4 runner/controls (`16e6d60`); D5 analysis/replay (`4375d93`).
- D1 proven on Colima: internal labnet, opaque mocks/DNS, hardened self-verified proxy, raw-IP/IPv6/nonce/
  positive-control checks, periodic topology canary, pause/kill test, four-layer telemetry, hygiene, DESTROY.
- Three local 3-agent/3-step smoke conditions complete (`smoke-treatment-001`, `smoke-isolated-001`,
  `smoke-no-impossible-001`), all phases 0/1 and all unscored. Ollama 3B experiment + 7B cold-audit models
  are local; no weights/telemetry committed. See `docs/SMOKE_REPORT.md`.
- Gates proven: missing audit stops before agent creation; dead depot freezes; direct target/gateway/raw-IP
  probes fail; second network is detected; isolation hides one agent's object from another; replay/report
  generation works. Independent red-team/researcher-repro subagents are still pending.

## Next action (where to start)
1. ~~Apply docs, build D1–D5, and smoke the full local pipeline~~ **DONE**.
2. Run independent containment red-team + researcher-repro reviews; fix findings without behavior-nudging.
3. Funded phase only: validate the zero-hole GPU-VM seal, use `/loop` for fixed-N unattended conditions,
   execute the frozen capability ladder/pre-post-cutoff comparisons (~60 clean runs for the tight-null target).
   OpenRouter would require a separate inference-egress deviation sign-off.

## Containment flag to keep visible
Local model-proxy = **one controlled, verified egress hole** (agents → proxy → host ollama). It keeps
everything on-box but makes the local seal **strictly weaker** than the GPU-VM seal (model in-lab, zero
holes). State this honestly in any report; validate the clean air-gap claim on the VM.
