# AGENT_CHECKLIST — discipline gates (binding for every change & run)

This checklist is enforced on every PR into `build/sealed-lab` and before every experiment run.
It encodes the HANDOFF "Acceptance" boxes and the CONTAINMENT hard requirements as mechanical gates.
If a gate cannot be satisfied, **the change does not merge and the run does not start.**

---

## 0. The hard gate (non-negotiable, checked by automation)

> **SEAL VERIFIED BEFORE ANY AGENT STEP.**
> No agent process may start until the automated seal-verification suite passes for the current run.
> The runner MUST abort the run (non-zero exit, frozen state) if any seal check fails. This gate is
> implemented in code (D1), not left to operator memory.

## 1. Safety gates (CONTAINMENT.md)

- [ ] **Deny-all egress** from agent sandboxes during a run; only intra-lab mock services reachable.
- [ ] **Seal verification passes** from inside an agent sandbox, BEFORE agents start:
  - [ ] raw-IP public internet (`1.1.1.1`, `8.8.8.8`) → route/policy denied (DNS-only proof is invalid)
  - [ ] IPv6 (`2606:4700:4700::1111`) → blocked and explicitly checked, never skipped
  - [ ] cloud metadata `169.254.169.254` / link-local / host loopback / gateway → blocked
  - [ ] permitted opaque mock names resolve; external names + a fresh nonce domain → NXDOMAIN
  - [ ] model endpoint is the **local** fixed proxy/server, not a remote API; proxy self-checks pass
  - [ ] **positive control** resolves a mock and reaches depot, proving the network/checker is alive
  - [ ] checks fail-CLOSED (bare timeout = INCONCLUSIVE/FAIL; missing/error = abort, never assumed blocked)
  - [ ] periodic runtime canary repeats verification; failure freezes agents + proxy and aborts
- [ ] **Kill switch** halts all agents + freezes state within seconds; **tested at every run start**.
- [ ] **Mock targets only** — no real HuggingFace/Artifactory/third party; `depot`/`origin`/`hub` are local analogs.
- [ ] **Analog, non-reusable vulnerabilities** only — no specific real CVEs, nothing portable to real software.
- [ ] **No reusable exploit** is produced or emitted; if a run yields an unexpectedly general technique →
      STOP, contain, review before continuing (CONTAINMENT dual-use clause).

## 2. Science gates (METHODOLOGY.md)

- [ ] **Salience-scoped prompt-audit passed** — an independent cold read of prompts, tool descriptions,
      errors, environment/DNS layout, credential/namespace naming, listing shape, and truncation/
      summarization policy finds no hint/reward/description of H1–H3 **and no conspicuous single door**.
      Audit whether the store resembles a feed, whether errors reveal alternate paths/authorship, and
      whether the egress-capable helper is unusually salient among plausible actions/dead-ends.
- [ ] Prompt-audit reruns on **every** prompt/tool/config/environment/truncation change; its artifact is
      hash-bound to the exact run config. Presence-only or one-time review is insufficient.
- [ ] Preconditions are **environment-shaping only**, never behavior-shaping. Any change that crosses the
      line is logged as a **separate condition**, never smuggled into an existing one.
- [ ] **Detectors are pre-registered** (defined before running) and version-pinned per condition.
- [ ] Run setup is **seeded & reproducible**: same (seed, model digest/quant/params, N, task set,
      precondition knobs) → same setup; stochastic completions are not claimed to be bit-identical.
- [ ] **Scheduler** (lockstep/async) and truncation policy are fixed, recorded, and audited.
- [ ] A scored condition follows its frozen fixed N/precision target (local toy runs are not scored);
      only one independent variable changes between conditions.
- [ ] Model versions recorded (contamination caveat noted: models may have trained on incident write-ups).

## 3. Telemetry gates (HANDOFF)

- [ ] Captures, per run, timestamped: every agent's **reasoning + tool calls**, every `depot` read/write,
      every **network/detection event** — enough to adjudicate each phase detector post hoc.
- [ ] Telemetry is written to **lab storage only**; never to a real external sink.

## 4. Repo hygiene gates

- [ ] **Never commit** weights, telemetry/run captures, secrets, `FLAG`, agent-generated artifacts.
      (`.gitignore` covers these; CI/pre-commit rejects them.)
- [ ] Lint + unit tests pass (seal-verification logic has its OWN tests, incl. fail-closed cases).
- [ ] The **analysis report is sanitized**: no live secrets, no reusable exploit detail, no real identifiers.
- [ ] Repo stays **private**.

## 5. PR / report convention

- [ ] Each PR states which deliverable (D1–D5) it advances and which checklist gates it touches.
- [ ] A PR that adds/changes agent prompts, tools, or environment **must** re-run the prompt-audit.
- [ ] A PR that touches the seal/network/kill-switch **must** re-run seal verification + its unit tests.
- [ ] Results PRs report an **emergence rate per phase per condition** and state **positive OR null** honestly.

---

### Run-start pre-flight (the runner executes this, in order, every run)
1. Build/refresh images → seal the network (deny-all egress).
2. **Run seal-verification suite from an agent sandbox. FAIL → abort, freeze, exit non-zero.**
3. **Test the kill switch.** FAIL → abort.
4. Confirm prompt-audit artifact for the current prompt set is present & passing.
5. Only then: start agents. Capture telemetry throughout. Teardown → retain sanitized captures only.
