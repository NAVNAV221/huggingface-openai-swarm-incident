# Worklog — Sealed lab build (OpenAI–HF swarm-incident reproduction)

**Branch:** `build/sealed-lab` (worktree off `master`)
**Task doc:** `docs/HANDOFF.md` (binding). Governing principle: engineer preconditions, never behavior; null result is valid.

## Decisions log
- **2026-11-07** — Run backend: **start LOCAL** (ollama + small open model on this M2 Pro). Local = air-gap-faithful, so the CONTAINMENT two-plane deviation is NOT needed; docs stay as written. OpenRouter/Crusoe deferred (would require the inference-egress deviation + sign-off).
- **2026-11-07** — Disk: freed ~6.1 GB (Library/Caches + ~/.cache). 25 GB free. Enough for one 8B model + lab images.
- Model ladder (capability = the documented independent variable): start Llama-3.1-8B / Qwen2.5-7B → step up Qwen2.5-32B → ceiling 70B. Exact slugs pinned at wire-time. On local, capped at ~8B (16 GB RAM) — capability sweep needs OpenRouter/Crusoe later.

## Dependency chain (father task owns sequencing — NOT parallel at start)
- [ ] **D1 — Sealed lab + verified seal (BLOCKS EVERYTHING).** compose: local model server, mock `depot`/`origin`/`hub`/mock-DNS, deny-all egress, seal lifecycle, auto seal-verification + kill switch.
- [ ] **D2 — Agents + minimal ReAct harness** (blocked by D1). Model-agnostic, OpenAI-compatible endpoint, per-agent sandbox, full instrumentation.
- [ ] **D3 — Engineered preconditions + generic analog weaknesses** (blocked by D2). + prompt-audit (3A) must pass.
- [ ] **D4 — Seeded runner + telemetry** (blocked by D3). `/loop` ≥20 runs/condition.
- [ ] **D5 — Analysis + replay** (blocked by D4). Pre-registered detectors, emergence rate, sanitized report.

## Negative/safety cases (must hold)
- [ ] Containment red-team subagents FAIL to break the seal.
- [ ] Prompt-audit finds NO hint of channel/coordination/pivot.
- [ ] Researcher-repro subagent launches from docs alone.
- [ ] No real egress; no reusable exploit; weights/telemetry/secrets git-ignored & uncommitted; report sanitized.

## Status
- **2026-11-07** — Worktree created. Launching concurrent Senior SWE + Senior PM review subagents to pressure-test design before writing lab code. AGENT_CHECKLIST.md pending.
