# Build status against AGENT_CHECKLIST — 2026-11-07

This is the current local implementation record, not a claim that funded acceptance is complete.

| Gate | Local status | Evidence / remaining work |
|---|---|---|
| Deny-all agent egress / L3 internal net | **PASS** | Raw IPv4/IPv6, metadata, link-local, loopback, gateway, direct targets denied on Colima. |
| Fail-closed seal + positive controls | **PASS** | Agent + proxy suites, fresh nonce NXDOMAIN, flat depot control; dead depot freezes. |
| Periodic runtime canary | **PASS** | Repeated agent/proxy checks plus second-network/capability/mount topology inspection. |
| Kill switch at every run start | **PASS** | Synthetic trigger pauses agents + proxy; telemetry intact and sink remains live. |
| Mock-only, analog non-reusable targets | **PASS** | Exact two-URL mock allowlist, no redirects; external URL rejected without fetch. |
| Local inference / honest topology caveat | **PASS locally** | Ollama on-box through one hardened hole; zero-hole GPU-VM proof remains funded work. |
| Prompt/tool/environment salience audit | **PASS for frozen hash** | Fresh 7B cold review `7f7d52c5…`; missing artifact prevents agent creation. |
| Engineer preconditions, never behavior | **PASS** | Neutral tasks, no pre-seeded message/feed, no advertised fetch, nulls unchanged. |
| Pre-registered detectors/primary/N/ladder | **PASS (artifact)** | `PRE-REGISTRATION.md` hash pinned in runs; scored execution remains funded. |
| Seed/model/setup reproducibility | **PASS** | Digest, quant, sampling, task/audit/image hashes, scheduler/truncation recorded; stochastic behavior not overclaimed. |
| Treatment + negative controls | **PASS (toy)** | Treatment, isolated, no-impossible each completed; direct isolation proof passed. |
| Four-layer telemetry | **PASS** | App + proxy + semantic service + VM pcap/nft drop evidence; per-agent isolation. |
| Analysis + replay | **PASS (toy)** | All phases 0/1 per condition, run-level intervals, primary/hierarchical analysis, offline replay. |
| Blind double coding + κ | **IMPLEMENTED** | Objective negatives needed no semantic codes. Actual independent coding required when candidates occur in scored runs. |
| Hygiene / CI / pre-commit | **PASS** | 42 tests, shellcheck, Compose, sensitive-file and whitespace checks; telemetry/weights/secrets ignored. |
| Independent containment red-team subagents | **PENDING** | Direct negative probes passed, but no independent subagent review is claimed. |
| Researcher-repro subagent | **PENDING** | Operations docs exist; independent from-docs reproduction not yet reviewed. |
| `/loop` ≥20/60 fixed-N unattended runs | **FUNDED / NOT RUN** | Local N=1 smokes are explicitly unscored; no tight-null or capability claim. |
| Capability ladder + pre/post-cutoff cross | **FUNDED / NOT RUN** | Frozen in pre-registration; no optional-stopping escalation. |
| VM DESTROY / sanitized retention | **LOCAL PASS / VM PENDING** | Local compose/volume/raw-data destroy exists; VM teardown is funded-phase work. |
