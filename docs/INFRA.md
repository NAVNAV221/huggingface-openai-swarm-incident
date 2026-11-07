# Infrastructure, model serving & cost

Constraints: **true air-gap** (local inference), **open models** (Qwen/Llama), short runs. Development
starts locally on the 16 GB M2 Pro with Colima + ollama and **3–4 agents plus a small quantized model**;
the funded 6–8-agent capability runs use a rented GPU. Local smoke tests are not full-scale evidence. The
seal lifecycle in `CONTAINMENT.md` is what keeps a rented cloud VM air-gapped.

---

## Serving stack

- Serve an open model with **vLLM** (OpenAI-compatible endpoint) on the rented GPU VM, or **ollama on the
  macOS host** for local development. Agent base URLs are `http://model-proxy:11434/v1` locally and
  `http://model:8000/v1` on the VM — **never** `localhost` (that is the agent container) and never a
  remote API. Do not "fix" this by giving agents host/network egress: the local proxy is the only hole.
- One model instance serves all agents. Weights are a fixed VRAM/RAM cost; the KV cache grows with
  concurrency × context length. The 16 GB local machine is limited to 3–4 agents and a small quant, and
  ollama may serialize requests. On a GPU, read vLLM's startup log for the real concurrency ceiling and
  set `--gpu-memory-utilization` accordingly.
- Pin and log the model identifier, **immutable digest, quantization**, and sampling parameters
  (`temperature`, `top_p`, `seed`, context length) in every run config. Sampler seeds are honored only if
  the serving backend supports them; neither ollama nor vLLM promises bit-identical behavior across
  batching/hardware. **Reproducible means deterministic setup and i.i.d. behavioral draws, not
  deterministic completions.**

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

- **docker-compose**: agent sandboxes, mock services (`depot`, `origin`, `hub`, mock DNS), telemetry,
  and either the in-lab `model` service (VM) or the dual-homed, egress-locked `model-proxy` (local).
  Agent sandboxes attach only to the `internal: true` network and have no default route out.
- Per-run config (seed, model, N, task set, precondition knobs) drives the **runner** so runs are
  reproducible (METHODOLOGY). Use `/loop` to execute the ≥20 seeded runs per condition unattended.
- Keep the VM region/size in the run config so cost and reproducibility are both recorded.
