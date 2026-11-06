# Infrastructure, model serving & cost

Constraints: **true air-gap** (local inference), **no local GPU** (rent one), **open models**
(Qwen/Llama), **~6–8 agents**, short runs. The seal lifecycle in `CONTAINMENT.md` is what keeps a rented
cloud VM air-gapped.

---

## Serving stack

- Serve an open model **locally on the rented GPU VM** with **vLLM** (OpenAI-compatible endpoint) or
  **ollama**. The agents' ReAct loop points at `http://localhost:<port>/v1` — **never** a remote API.
- One model instance serves all 6–8 agents. Weights are a fixed VRAM cost; the KV cache grows with
  concurrency × context length — 6–8 agents with modest context is light. Read vLLM's startup log for the
  real concurrency ceiling at your context length and set `--gpu-memory-utilization` accordingly.

## Model & GPU sizing (start cheap, scale as a documented variable)

| Tier | Model (open) | Fits on | Rough VRAM | Use |
|---|---|---|---|---|
| Iterate | Qwen2.5-14B-Instruct / Llama-3.1-8B | L40S 48GB | ~20–30 GB (FP8) | cheap first runs |
| Step up | Qwen2.5-32B-Instruct | A100 80GB | ~40 GB (FP8) + KV | if small models show no spark |
| Ceiling | larger (e.g. 70B) | H100 80GB / 2×A100 | ~90 GB (FP8) | last capability lever |

Capability is the sanctioned lever when emergence doesn't appear (see METHODOLOGY). Raising it is a
*documented variable*, never a substitute for the agents doing it themselves.

## Cost (rough — confirm live before spending; trackers disagree)

Per GPU-hour, on-demand, billed by the minute/hour and **torn down between runs**:

| Provider | L40S 48GB | A100 80GB | H100 80GB |
|---|---|---|---|
| Crusoe | ~$1.00–1.50 | ~$2.00–2.30 | ~$3.90 |
| RunPod | — | ~$1.39–1.59 | ~$2.69–3.29 |
| Vast.ai (marketplace) | — | ~$0.34–1.30 | ~$2.14 |

A full day of experimentation on an L40S/A100 is roughly **$10–50**. Confirm current rates on the
provider's own pricing page; Crusoe is a fine default, RunPod/Vast are cheaper. Sources (Nov 2026,
secondary — verify): Crusoe pricing trackers, RunPod/Vast/Lambda comparison blogs (see REFERENCES).

## Air-gap on a rented box (the only subtle part)

Egress is needed exactly **once**, to pull weights + build images (seal lifecycle step 2). After that,
**deny-all egress** is enabled and **verified** (CONTAINMENT "Verify the seal") before any agent runs.
Because the model is served on the same VM, sealing egress does **not** break inference. Destroy the VM
after capturing telemetry; keep only the sanitized report + run data.

## Lab environment

- **docker-compose** on the VM: the agent sandboxes, the mock services (`depot`, `origin`, `hub`, mock
  DNS), the local model server, the telemetry sink. One internal network, default-deny egress.
- Per-run config (seed, model, N, task set, precondition knobs) drives the **runner** so runs are
  reproducible (METHODOLOGY). Use `/loop` to execute the ≥20 seeded runs per condition unattended.
- Keep the VM region/size in the run config so cost and reproducibility are both recorded.
