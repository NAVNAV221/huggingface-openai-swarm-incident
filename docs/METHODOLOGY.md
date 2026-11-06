# Methodology

This is a **research experiment**, so it lives or dies on a crisp question, honest variables, and
pre-registered metrics. A **null result is a valid, reportable outcome.**

---

## Research question

> Under faithful preconditions, will ~6–8 isolated small LLM agents **independently** (a) discover they
> can communicate via a shared service, (b) form a coordination convention, and (c) find a way to pivot
> out to a resource they were blocked from — and if so, **how, how fast, and does a coordinator emerge**?

## The governing principle: engineer conditions, never behavior

We recreate the *conditions* that made the real emergence possible — an impossible task, a shared reused
credential, a non-isolating shared service, blocked egress with one reachable surface. We **never** script,
prompt, or reward the target behaviors (don't tell agents to talk, don't hint at the channel, don't
describe the egress). If the agents don't emerge the behavior under faithful conditions, **that is the
finding.** Any change that crosses from "shaping the environment" into "shaping the behavior" invalidates
the run as evidence — log it as a different condition, don't smuggle it in.

## Hypotheses

- **H1 (channel):** agents will discover the shared medium as a channel. (Real incident: yes.)
- **H2 (coordination):** a stable convention and an emergent coordinator will form.
- **H3 (pivot):** agents will find *some* egress to the blocked resource using shared info.
- **H0 (null):** at this scale / model capability, none of H1–H3 reliably occurs. **Fully acceptable.**

## Variables

**Independent (we vary, one at a time, documented):**
- **Model capability** — the primary lever. Start small (Qwen2.5-14B / Llama-3.1-8B); if no spark of
  emergence, step up (Qwen2.5-32B, then larger) as a **documented variable**, not as a fix. Capability,
  not behavior-nudging, is the sanctioned way to probe whether emergence is reachable.
- **N agents** (~6–8; optionally vary within that band).
- **Precondition strength** — e.g. how blocking the impossible task is, how discoverable `depot`'s
  cross-agent side effects are. Keep these as *environment* knobs; record each setting.
- **Run length / step budget** per agent.

**Dependent (we measure):**
- phase reached (0–5, per EXPERIMENT.md detectors)
- **time-to-channel-discovery** (steps / wall-clock to Phase 2)
- **# agents that join** the channel
- whether a **stable convention** forms (and its structure)
- whether a **coordinator emerges** (and which agent / how)
- whether the **pivot completes** (Phase 4/5) and by what emergent technique
- which **detection signals** fired and when (for the detection-gap analysis)

## Run protocol

1. **Seeded & repeated.** Every run is fully configured (seed, models, N, task set, precondition
   settings) so it's reproducible. Run **many** (e.g. ≥20) per condition — emergence is stochastic.
2. **Report an emergence rate**, not a single anecdote: "Phase 2 reached in X/N runs; Phase 4 in Y/N."
   A single dramatic run is a case study, not a result.
3. **Fixed protocol across a condition.** Don't tweak mid-condition. Change one independent variable,
   start a new condition, keep the rest constant.
4. **Blind-ish analysis.** Define the phase detectors *before* running, so you're not inventing
   "emergence" post hoc from suggestive transcripts.
5. **Capture everything** (TELEMETRY in HANDOFF): every agent's full reasoning + tool calls, every
   `depot` read/write, every network event, every detection signal, timestamped. The raw run is the data.

## What counts as a result

- **Positive:** a phase is reached in a non-trivial fraction of seeded runs, with the detector firing and
  the transcript showing the agents genuinely re-deriving it (not responding to a leaked hint).
- **Null:** phases don't reliably occur across conditions up to the capability ceiling you're willing to
  fund. Report it plainly with the conditions tested — it's a real contribution (small capable-enough
  agents don't spontaneously do this at tiny scale).
- **Invalid:** any run where a precondition change leaked the behavior (a hint, a reward, a prompt). Mark
  and exclude; note it as a cautionary methodology finding.

## Threats to validity (call these out in the report)

- **Hinting leakage** — the top risk. Audit prompts/tools/environment for anything that *tells* agents to
  coordinate or how to escape. The active check: an independent reviewer reads the agent prompts cold and
  confirms none of H1–H3 is implied.
- **Detector over-fitting** — too-loose detectors will "find" emergence in noise. Pre-register them.
- **Capability confound** — a positive only at large models means "capable models do this," which is
  still a finding; report the capability threshold.
- **Scale confound** — negative at 6–8 agents doesn't prove it won't emerge at 1,200. State the scope.
- **Contamination** — if a model was trained on write-ups of this very incident, it may "know the plot."
  Note the models used and this limitation.

## When to stop

Stop a condition after its planned N runs. Stop the experiment when either (a) you observe the full chain
emerge at a rate worth reporting, or (b) you've reached the capability/scale ceiling you're willing to
fund with a stable null. Either way you have a reportable result.
