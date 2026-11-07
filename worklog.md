# Worklog — Sealed lab build (OpenAI–HF swarm-incident reproduction)

**Branch:** `build/sealed-lab` (worktree off `master`)
**Task doc:** `docs/HANDOFF.md` (binding). Governing principle: engineer preconditions, never behavior; null result is valid.

## Decisions log
- **2026-11-07** — Run backend: **start LOCAL** (ollama + small open model on this M2 Pro). Local = air-gap-faithful, so the CONTAINMENT two-plane deviation is NOT needed; docs stay as written. OpenRouter/Crusoe deferred (would require the inference-egress deviation + sign-off).
- **2026-11-07** — Disk: freed ~6.1 GB (Library/Caches + ~/.cache). 25 GB free. Enough for one 8B model + lab images.
- Model ladder (capability = the documented independent variable): start Llama-3.1-8B / Qwen2.5-7B → step up Qwen2.5-32B → ceiling 70B. Exact slugs pinned at wire-time. On local, capped at ~8B (16 GB RAM) — capability sweep needs OpenRouter/Crusoe later.

## Dependency chain (father task owns sequencing — NOT parallel at start)
- [x] **D1 — Sealed lab + verified seal (BLOCKS EVERYTHING).** Colima compose, mock depot/origin/hub/DNS,
  internal labnet, hardened/self-verified model-proxy, raw-IP/IPv6/nonce/positive-control verification,
  periodic topology canary, pause kill switch, 4-layer telemetry, hygiene hooks, local DESTROY.
- [ ] **D2 — Agents + minimal ReAct harness** (blocked by D1). Model-agnostic, OpenAI-compatible endpoint, per-agent sandbox, full instrumentation.
- [ ] **D3 — Engineered preconditions + generic analog weaknesses** (blocked by D2). + prompt-audit (3A) must pass.
- [ ] **D4 — Seeded runner + telemetry** (blocked by D3). `/loop` ≥20 runs/condition.
- [ ] **D5 — Analysis + replay** (blocked by D4). Pre-registered detectors, emergence rate, sanitized report.

## Negative/safety cases (must hold)
- [x] D1 direct negative probes fail: public/raw IPv4+IPv6, metadata/link-local/loopback/gateway, direct
  origin/hub, real DNS names, proxy arbitrary routes. Runtime second-network injection is detected.
  Independent red-team subagents remain pending (no experiment agent has run).
- [ ] Prompt-audit finds NO hint of channel/coordination/pivot.
- [ ] Researcher-repro subagent launches from docs alone.
- [ ] No real egress; no reusable exploit; weights/telemetry/secrets git-ignored & uncommitted; report sanitized.

## Status
- **2026-11-07** — Concurrent Senior SWE + PM reviews reconciled; §C1 docs and frozen pre-registration
  committed as `7c07565`.
- **2026-11-07 — D1 PASS on Colima (`seal-20261107-d1`).** `lab/bin/up.sh` completed with no experiment
  agents; agent and proxy suites passed, repeated periodic canaries passed, pcap + actual nftables drop
  records were captured, and synthetic anomaly pause preserved canary telemetry.
- **Fail-closed proof:** stopping depot made verification fail and froze the proxy. Initial live gaps
  (telemetry permissions, gateway reachability, stale target firewall) likewise prevented startup until
  fixed. A deliberately attached second internal network failed the host topology check.
- **Static gates:** 16 unit tests, Compose validation, shellcheck, hygiene, and `git diff --check` pass.
- **Next:** D2 text ReAct/parser + fixed scheduler/truncation + local ollama smoke with 3–4 agents maximum.
  D3 prompt/precondition work and D4/D5 scored infrastructure remain sequential. Scored runs/capability
  ladder/~60-run power stay funded-phase work. The local proxy is one controlled, strictly-weaker hole;
  clean zero-hole air-gap claims require the VM topology.
