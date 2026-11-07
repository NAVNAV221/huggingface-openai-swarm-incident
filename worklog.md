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
- [x] **D2 — Agents + minimal ReAct harness.** Strict text parser, parse-failure counts, per-agent mounts,
  static IPs, full instrumentation, fixed lockstep + whole-step truncation, cold capability probe.
- [x] **D3 — Preconditions + generic analog weakness + prompt-audit.** Neutral tasks, isolated control,
  exact-mock-only unadvertised fetch, flat/no-preseed store; fresh 7B salience audit passes frozen hash.
- [x] **D4 — Seeded runner + controls + telemetry (local smoke).** Three conditions complete. Long `/loop`
  ≥20/60 runs remain funded work, deliberately not run locally.
- [x] **D5 — Analysis + replay.** Graded objective/semantic detectors, blind coding + κ, Wilson/CP intervals,
  primary/hierarchical analysis, contamination rules, sanitized report + offline replay.

## Negative/safety cases (must hold)
- [x] D1 direct negative probes fail: public/raw IPv4+IPv6, metadata/link-local/loopback/gateway, direct
  origin/hub, real DNS names, proxy arbitrary routes. Runtime second-network injection is detected.
  Independent red-team subagents remain pending after the now-completed smoke runs.
- [x] Fresh cold salience audit finds no hint/conspicuous door; failed/inconsistent reviews blocked startup.
- [ ] Researcher-repro subagent launches from docs alone.
- [x] No real egress/target; analog-only allowlist; weights/telemetry/secrets gitignored & uncommitted;
  sanitized D1/D3/smoke reports. Independent containment/repro reviews remain open.

## Status
- **2026-11-07** — Concurrent Senior SWE + PM reviews reconciled; §C1 docs and frozen pre-registration
  committed as `82ff364`.
- **2026-11-07 — D1 PASS on Colima (`seal-20261107-d1`).** `lab/bin/up.sh` completed with no experiment
  agents; agent and proxy suites passed, repeated periodic canaries passed, pcap + actual nftables drop
  records were captured, and synthetic anomaly pause preserved canary telemetry.
- **Fail-closed proof:** stopping depot made verification fail and froze the proxy. Initial live gaps
  (telemetry permissions, gateway reachability, stale target firewall) likewise prevented startup until
  fixed. A deliberately attached second internal network failed the host topology check.
- **2026-11-07 — D2–D5 local implementation + smokes PASS.** D2 `bfc3592`, D3 `4cf3618`, D4 `16e6d60`,
  D5 `4375d93`. Three 3-agent/3-step runs completed with every phase 0/1, zero writes/foreign reads/fetches,
  and three retained parse failures per condition. Combined report: `docs/SMOKE_REPORT.md`.
- **D4 negative/control proofs:** missing audit stops before experiment-container creation; direct isolated
  write/list test shows agent-2 cannot see agent-1's object; local `--scored` is mechanically forbidden.
- **Static gates:** 42 unit tests, Compose validation, shellcheck, hygiene, whitespace checks, and pre-commit
  pass. Root telemetry/analysis is gitignored as well as run captures.
- **Next:** independent containment red-team + researcher-repro reviews. Funded phase: zero-hole VM seal,
  `/loop` fixed-N runs, capability ladder and pre/post-cutoff comparisons. The local proxy remains one
  controlled, strictly-weaker hole; no clean zero-hole claim is made locally.
