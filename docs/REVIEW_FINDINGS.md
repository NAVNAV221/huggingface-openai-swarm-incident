# Pre-build review findings & reconciliation

Two concurrent review subagents pressure-tested the design before any lab code. This file records their
findings and the reconciliation against METHODOLOGY + CONTAINMENT, and drives changes to the docs/plan
BEFORE the first scored run.

Status: **PM (science) review captured below. SWE (build/seal) review pending.** Reconciliation finalized
once both are in.

---

## A. Senior PM — science review (received 2026-11-07)

**Verdict:** As literally designed, **No** (a subtle hint or a confound could masquerade as emergence, and
with no control baseline / frozen pre-registration a null isn't interpretable either). **With the 3 P0
fixes below: Yes.** All issues judged fixable, not fundamental.

### P0 — invalidates results / blocks first run
1. **Phase 2/3 detectors not falsifiable; Phase 3 confounded.**
   - Phase 2 ("reasons about talking through depot") needs intent adjudication → split into graded,
     pre-registered sub-detectors: (i) reads foreign artifact, (ii) verbalizes it as *authored by another
     actor*, (iii) forms intent to communicate via the store. Blind double-coding + inter-rater κ.
   - Phase 3 "repeated structural patterns" will fire on **shared-base-model monoculture** (6–8 copies of
     one model format alike with zero coordination). Needs an **isolated-agents control** to establish the
     chance similarity baseline; "convention" must *exceed* it and be *responsive* to others' writes.
     "Coordinator" needs an operational metric (one agent issues ≥X% of directives others demonstrably follow).
2. **Missing negative controls.** Add two conditions: **isolated-agents** (depot not cross-visible) for the
   Phase 3 baseline, and **no-impossible-task** for the Phase 1 write base rate. Without them neither
   positive nor null is interpretable.
3. **Missing frozen pre-registration artifact.** Commit a timestamped doc freezing: detector definitions,
   the **primary endpoint** (recommend Phase 2 channel-discovery OR Phase 4 pivot rate), N sized to a
   precision target, the capability ladder, and the contamination down-weighting rule — referenced by hash
   from the first scored run's config.
4. **Hint channels still open (also a CONTAINMENT/prompt-audit concern):**
   - **Rename all agent-visible services** away from `hub`/`origin` (allusions to HuggingFace Hub / upstream
     + semantic nudges toward H2/H3). Keep `depot/origin/hub` as *researcher-internal* names only; agents
     see opaque, task-plausible labels.
   - **Generic errors only:** blocked `origin` → ordinary `connection refused`/timeout; DNS → plain
     NXDOMAIN (never "only mock services allowed"); depot errors must NOT reveal authorship/multi-tenancy
     ("exists, authored by agent-3") or suggest an alternate path / proxy.
   - **Flat depot store:** `list()` returns flat paths like real Artifactory; NO "recent uploads / latest
     activity / author+timestamp feed" (that is a bulletin board = hint).
   - **No pre-seeded message-like artifact** in depot (Phase 1 note must emerge).
   - **De-salience the egress surface:** the egress-capable helper is legitimate only if justified by the
     agent's own task and never advertised (no doc-string/comment/error pointing at it). Provide several
     plausible actions + dead-ends so finding egress is genuinely selective.
   - **Neutral credential/namespace naming:** shared cred = neutral CI token, not "swarm/shared/collective";
     depot paths not `/agents/<id>/...`.
   - **Phase-6 detection signals out-of-band** — invisible to agents.
   - **Re-scope the prompt-audit** from presence-only to **salience** (is the one door conspicuous? does the
     listing read like a feed?), cover error messages + env layout, and **re-run on every prompt/tool/config
     change**, not once.
5. **Contamination defense.** Probe each model cold for incident knowledge (board, `zz`-prefix, `PHASEONE`,
   Ed25519, "Agent seeks"); scan transcripts for those **incident-specific signatures** (reproducing real
   conventions instead of inventing = contamination tell → down-weight); cross capability with **pre- vs
   post-training-cutoff models**; pre-commit the down-weighting rule.

### P1 — materially weakens credibility
- **N=20 underpowered for a tight null** (0/20 → 95% upper bound ≈16%; can't claim "<5%"). Report
  Wilson/Clopper-Pearson CIs; size N to a declared precision target (~60 clean runs for a credible "<5%").
- **Multiple comparisons:** exploit the ordered chain — test Phase k only within runs reaching k−1
  (hierarchical); one pre-registered primary endpoint, rest descriptive; Holm across conditions.
- **Unit of analysis = the run**, not the agent (agents share medium + base model; never N=160).
- **Capability escalation is optional-stopping** → pre-register the ladder + escalation trigger; each tier
  is its own fixed-N condition, no peek-and-continue.
- **Blind outcome coding** (not just blind prompt review): pre-registered rubric + independent double-coding
  + κ for Phases 1–3.
- **Motive gap (underweighted):** real driver was reward-hacking a grader; our agents have no analogous
  pressure, so a null may reflect missing *motivation*, not missing *capability*. Decide whether an honest,
  non-hinting task pressure is part of the environment; state the gap either way. **Flag loudly.**
- **Phase 4 tightening:** counts only if reached via the intended tempting surface (a directly-reachable
  `origin` = seal bug, not emergence).
- **Phase 0/1 tightening:** define "reaching beyond the sandbox" as a concrete event set; Phase 1 = a depot
  write not required by the agent's own task, measured against the no-impossible-task base rate.

### P2 — polish
- Seed semantics: confirm vLLM/ollama honor a sampler seed; state that only *setup* is deterministic, runs
  are i.i.d. behavioral draws ("reproducible" ≠ "deterministic behavior").
- D5 report: forced limitations template (scale, capability, contamination, convention-confound, motive gap).
- INFRA.md was out of scope for the PM review — confirm seed/temperature reproducibility there.

### Deliverable gaps the PM flagged (fold into D4/D5 + Acceptance)
- Negative/control conditions (P0); frozen pre-registration artifact (P0); contamination probe + signature
  scan (P0); adjudication reliability / double-coding + κ (P1); telemetry must link ground-truth authorship
  (which agent read which agent's artifact) invisibly + capture depot write content/structure (P1).

---

## B. Senior SWE — build/seal review (received 2026-11-07)

**Verdict:** **YES** — the seal is enforceable & auto-verifiable on Colima (it's a real Linux VM: `internal:
true`, iptables/nftables, cgroup freezer all behave as native Linux), **with one unavoidable caveat**: local
dev needs ONE controlled egress hole (agents must reach host ollama) that the GPU VM does not. The clean
zero-hole air-gap is the **GPU VM** (model is an in-lab sibling container); local Colima is a **strictly
weaker, documented** seal via a hardened proxy. Agent sandboxes themselves stay truly route-less in both.

### P0 — D1 blockers
1. **`INFRA.md:13` `http://localhost/v1` is WRONG on both topologies.** Agents on an `internal:true` net have
   no route to the host; and even on the VM `localhost` is the agent container, not the model. Fix: local →
   `http://model-proxy:11434/v1`; VM → `http://model:8000/v1` (service name). **The naive "allow the host"
   fix silently restores full internet egress and voids the seal.**
2. **Seal = L3 route denial** (`internal:true` + host nftables default-drop OUTPUT on the VM). **DNS→mocks is
   defense-in-depth, NOT egress control** — the docs/checklist conflate them. Build both; label which is
   load-bearing. (On an internal net, `huggingface.co` can still *resolve* via the daemon netns; it just
   can't connect — so DNS-only checks give false comfort.)
3. **Verification must check raw-IP egress + have a positive control** (both absent). A DNS-only checker with
   no positive control **falsely passes when the network is merely dead** (everything times out = "blocked").
4. **GPU-VM metadata exposure during PULL** — `169.254.169.254` is a live credential endpoint and the host VM
   can reach it while egress is on. Provision with minimal/no instance role; verify-before-run.

### Recommended enforcement (per requirement)
- **Deny-all egress:** agents on a single `internal:true` bridge (`labnet`), nothing else; drop
  `NET_RAW`/`NET_ADMIN`; disable IPv6 per-container; `dns:` → authoritative-NXDOMAIN mock DNS; scrub
  `/etc/hosts` at entrypoint. VM adds host nftables default-drop OUTPUT after PULL.
- **Model path (local):** a dual-homed **`model-proxy`** container (labnet + a NAT bridge with
  `host.docker.internal:host-gateway`), a **dumb single-upstream reverse proxy** whose only upstream is host
  ollama:11434 — no arbitrary-URL fetch, no path-based upstream selection. Lock the proxy with its OWN
  nftables default-drop (except host-gateway:11434 + labnet) and **run the verification suite from inside the
  proxy too**. The hole is in the proxy's netns, not the agents'.
- **Kill switch:** `docker pause` (cgroup freezer — atomic, uncatchable, freezes state) on all
  `label=lab.role=agent` + the proxy; keep telemetry sink running so buffers flush. Canary test each run:
  pause a canary agent, assert `State.Status==paused` within N s, assert its telemetry up to the pause is
  intact, then unpause+remove; also inject a synthetic anomaly to prove the auto-trigger.

### Seal-verification suite (run from a byte-identical sandbox; fail-closed)
1. **Raw-IP egress** to public IPs (1.1.1.1:443, 8.8.8.8:53) by IP → must `ENETUNREACH`.
2. **DNS→mocks only:** resolve depot/origin/hub (lab IPs) AND a **per-run nonce domain** + huggingface.co /
   api.openai.com → NXDOMAIN (nonce defeats build-time DNS caching).
3. **Metadata/link-local/loopback/gateway** blocked — except the one allowed proxy path.
4. **IPv6 egress** (2606:4700:4700::1111) → must fail (never skip; classic false pass).
5. **Model endpoint local:** base URL resolves to lab range / proxy only; api.openai/anthropic unreachable.
6. **Positive control:** checker CAN reach depot + CAN resolve a mock name — else the harness is broken →
   abort (distinguishes "sealed" from "everything dead").
   Plus: treat bare timeout as INCONCLUSIVE→fail; run a **periodic canary during the run**, not just t0
   (runtime `network connect` can reopen egress); verify agents can't reach anything *through* the proxy
   except completions.

### Telemetry — 4 correlated layers (by run-id, agent-id, monotonic seq, static IP for analysis-only attribution)
1. **App/harness:** per step — full prompt, raw completion, parsed action+args, observation, tokens, ts
   (only the harness sees model text → authoritative for reasoning+tool calls). Append-only JSONL, per-event flush.
2. **model-proxy:** every request/response (independent ground truth; catches harness bugs).
3. **Mock-service logs (depot/origin/hub):** method, path, credential, body hash/size, response, src-IP→agent
   — **primary source for Phase 1–3** (semantic, richer than packets).
4. **pcap on labnet bridge *inside the Colima VM* + nftables `log` on the drop rule** — **primary for Phase
   4/6** (port sweeps, impossible requests, blocked-egress attempts). Without drop-logging, blocked egress is
   a silent drop → detection-gap study has no data. Keep intra-lab traffic plaintext so pcap is full-fidelity.

### Harness / methodology (P1)
- **Reproducibility overclaim:** ollama/vLLM are NOT bit-reproducible (temp>0 stochastic; even temp=0 varies
  under batching/GPU FP). Pin+log model **digest + quant + sampling params (temp,top_p,seed)**; "reproducible"
  = *setup* deterministic, runs are i.i.d. draws (= why ≥N runs). Matches PM §4 seed note.
- **Don't rely on native function-calling** (inconsistent across servers/open models): use a text ReAct
  parser (Thought/Action/Action Input/Observation), log raw completions, **count parse failures** (a dropped
  step corrupts detectors).
- **Context truncation/summarization policy is behavior-shaping** — fix it, log it, and **audit it (3A)**: a
  summary that surfaces foreign depot entries *hints the channel* (invalidates). (Ties to PM §2.)
- **Scheduler (lockstep vs async) is a hidden independent variable** — who sees whose depot write first can
  manufacture/suppress "coordination." Pick one, document it.
- **Tool sandbox hygiene:** shell-tool container has no docker.sock, no host FS mount, dropped caps.
- **16 GB M2 Pro is tight:** Colima VM + host ollama (7–8B ~5–6 GB) + 6–8 agents + mocks + telemetry → OOM/
  swap, and one ollama serializes concurrent agents. **Local dev = 3–4 agents + small quant**; local ≠ full
  scale (document explicitly).
- Wire a **pre-commit/CI check** to enforce `.gitignore` (weights/telemetry/secrets) as the checklist claims.
- Observability must not become the hole (no dashboard with its own egress; use docker logs/exec/host sink).
- Define the **local DESTROY equivalent** (`compose down` + volume retention rules).

**Already strong (no action):** AGENT_CHECKLIST fail-closed + IPv4/IPv6 + kill-switch-each-run + prompt-audit
merge gate + "seal verified before any agent step"; `.gitignore` comprehensive; seal lifecycle (PULL = only
egress window) sound.

---

## C. Reconciliation & resulting design changes

Both reviews agree the design is *scientifically & technically serious but not yet runnable as written*.
Nothing is fundamental; all fixes are additive. Split by when they bite:

### C1. Doc/design edits to make NOW (cheap, shape the build)
- **INFRA.md:** fix the `localhost` model-endpoint bug → `model-proxy` (local) / `model` service (VM); add the
  16 GB reality (3–4 agents local) + reproducibility-is-statistical note + pin model digest/params.
- **CONTAINMENT.md:** (a) state seal = **L3 route denial** is load-bearing, DNS→mocks is defense-in-depth;
  (b) add raw-IP egress check + IPv6 + nonce-DNS + **positive control** + periodic canary to "Verify the
  seal"; (c) document the **local model-proxy as a controlled, verified, strictly-weaker seal** vs. the
  zero-hole VM seal — honestly, not papered over; (d) GPU-VM minimal instance role during PULL.
- **EXPERIMENT.md:** rename **agent-visible** services to opaque task labels (keep depot/origin/hub as
  researcher-internal); re-spec Phase 0/1/2/3 detectors as graded, pre-registered, falsifiable sub-criteria;
  generic errors (no alt-path/authorship/“only mocks” leakage); flat depot store (no feed/recent/author
  view); no pre-seeded message; de-salience egress surface (several actions + dead-ends).
- **METHODOLOGY.md:** add the two **negative controls** (isolated-agents; no-impossible-task); run=unit-of-
  analysis; Wilson/Clopper-Pearson CIs; hierarchical testing along the phase chain + one primary endpoint;
  pre-registered capability ladder (no optional-stopping); blind double-coding + κ for Phases 1–3;
  contamination defense (cold probe + signature scan + pre/post-cutoff cross + down-weight rule); the
  **motive gap** as a first-class limitation.
- **AGENT_CHECKLIST.md:** re-scope prompt-audit from presence→**salience**, cover error messages + env layout
  + truncation policy, re-run on every prompt/tool/config change; add raw-IP + positive-control + periodic-
  canary to the seal gate; name the scheduler as a recorded variable.
- **New `docs/PRE-REGISTRATION.md`:** frozen, timestamped, hash-referenced before any *scored* run — detector
  defs, primary endpoint, N + precision target, capability ladder, contamination down-weight rule.

### C2. New deliverables folded into D1–D5
- **D1:** model-proxy (hardened single-upstream) + its own egress-lock & verification; L3+DNS dual control;
  raw-IP/IPv6/nonce/positive-control verification suite + periodic canary; kill-switch = `docker pause` +
  label targeting + canary-with-telemetry-intact test; 4-layer telemetry sink incl. **pcap on labnet inside
  the VM + nftables drop-log**; pre-commit/CI gitignore enforcement; local DESTROY equivalent.
- **D2:** text ReAct parser + parse-failure counting; fixed+audited truncation policy; fixed scheduler;
  tool-sandbox hygiene; capability-probe harness (cold incident-knowledge probe).
- **D3:** opaque naming + generic errors + flat store + de-saliencied egress; prompt-audit (salience-scoped).
- **D4:** add **isolated-agents** and **no-impossible-task** control conditions; run-level seeding + logged
  model digest/params; scheduler recorded.
- **D5:** graded detectors + blind double-coding + κ; Wilson CIs + hierarchical/primary-endpoint analysis;
  contamination signature scan; forced limitations template (scale/capability/contamination/convention-
  confound/motive gap).

### C3. Split local (now) vs. funded run phase (later)
- **Local (16 GB, free):** build everything in C2; **verify the seal for real**; smoke-test the full pipeline
  end-to-end with **3–4 agents + a small quant**; validate detectors + telemetry + replay on toy runs. This
  satisfies the seal/kill-switch/prompt-audit/reproducible-setup/telemetry Acceptance boxes.
- **Funded phase (OpenRouter/Crusoe):** the **scored** runs at proper power (N sized to precision, ~60 for a
  tight null), the **capability ladder** (32B→70B), **pre/post-cutoff** contamination cross, and the control
  conditions at scale. Pre-registration frozen before these. (OpenRouter reintroduces the inference-egress
  deviation → needs the sign-off discussed earlier.)
