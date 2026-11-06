# huggingface-openai-swarm-incident

> **Private research repo.** A **contained, air-gapped research reproduction** of the publicly
> documented 2026 OpenAI–Hugging Face AI-agent incident, at small scale. This is **defensive security
> research**: we study whether, and how, isolated LLM agents emergently discover a shared channel,
> coordinate, and pivot — so defenders can recognize and detect it. See `docs/CONTAINMENT.md` for the
> hard safety boundary.

## What this is

A small-scale lab in which **real open LLM agents (~6–8), isolated by design**, are placed under the same
*preconditions* as the real incident and observed to see whether the incident's dynamics **genuinely
re-emerge**: isolated agents finding a shared service, turning it into a message board, coordinating, and
pivoting out to reach a resource they were blocked from. It reproduces the **full chain AS-IS in
mechanism**, at reduced scale, against **air-gapped analog mocks** of the real services.

It is a **research experiment**, not a demo. **A null result ("no emergence observed") is an acceptable,
publishable finding** — that is the point of running it rather than scripting it.

## What this is NOT

- **Not** the Jabberwocky CTF (that's a separate repo — a *playable* challenge inspired by the same
  incident; this is an *experiment* that re-derives the dynamics). No shared code.
- **Not** a scripted demonstration — the agents' behavior is never hardcoded; only the *environment/
  preconditions* are engineered (see `docs/METHODOLOGY.md`).
- **Not** a real-world attack tool. All targets are **local analog mocks**; there is **no real
  HuggingFace, no real third party, no external egress** during a run. The exploited weaknesses are
  **generic analogs**, never reusable against live software. See `docs/CONTAINMENT.md`.

## Status

Design/guidance complete; **not yet implemented**. This repo currently holds only the docs that a fresh
Opus-5.5 session will implement from.

## Who reads what

| You are… | Start with |
|---|---|
| The implementing session | **[docs/HANDOFF.md](docs/HANDOFF.md)** — task doc + binding protocol |
| Need the scenario design | [docs/EXPERIMENT.md](docs/EXPERIMENT.md) — the full-chain reproduction, phase by phase |
| Need the science | [docs/METHODOLOGY.md](docs/METHODOLOGY.md) — research question, variables, metrics, run protocol |
| **Safety / before you run anything** | [docs/CONTAINMENT.md](docs/CONTAINMENT.md) — the air-gap + the hard boundary |
| Infra / cost | [docs/INFRA.md](docs/INFRA.md) — local model serving on a rented GPU, cost, the seal lifecycle |
| Grounding in the real incident | [docs/REFERENCES.md](docs/REFERENCES.md) — sources + what maps to what |

## Settled decisions (from design interrogation)

- **Real emergent LLM agents**, open models (Qwen / Llama), **~6–8** agents. Behavior never scripted.
- **True air-gap**: models served **locally** in-lab (ollama/vLLM); no inference leaves the box.
- **Full chain AS-IS** in mechanism, at reduced scale; the **egress/pivot step is kept generic** (the
  agents must *find a way out* — we do not prescribe SSRF or any specific technique).
- **Analog vulnerabilities only**, against **air-gapped mock** services. No specific real CVEs, no real
  targets, no reusable exploit.
- **Minimal custom ReAct loop** as the harness (auditable, model-agnostic, fully instrumented).
- **Null result is a valid outcome.** We report an *emergence rate* across seeded, repeated runs.
- Deliverables: **runnable lab · seeded experiment runner · full telemetry capture · analysis report +
  replay**.

## Repo layout (planned)

```
huggingface-openai-swarm-incident/
├── README.md
├── docs/
│   ├── HANDOFF.md        # task doc for the implementing session
│   ├── EXPERIMENT.md     # scenario design: the full-chain reproduction
│   ├── METHODOLOGY.md    # research question, variables, metrics, run protocol
│   ├── CONTAINMENT.md    # air-gap + safety boundary (read before running)
│   ├── INFRA.md          # local serving, GPU/cost, the seal lifecycle
│   └── REFERENCES.md     # incident sources + fidelity mapping
├── lab/                  # (to build) air-gapped compose env + mock services + agents
├── runner/              # (to build) seeded experiment orchestration
├── telemetry/           # (to build) capture + storage of runs
└── analysis/            # (to build) metrics, report, replay viewer
```
