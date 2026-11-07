# D2 agent harness

`harness.py` executes exactly one text-ReAct step per process. D4 invokes one step per agent in fixed
`agent-1…N` order per round (`lockstep-sequential-v1`), so visibility order is a recorded independent
variable rather than incidental async timing. Each sandbox has only its own config/state/app mount; it
cannot read other agents' telemetry.

- Strict `Thought / Action / Action Input` JSON parsing; raw completions and parse failures are logged.
- No native function-calling. Tools are package-cache reads/writes, bounded shell, and finish only.
- Fixed `drop-oldest-whole-steps-v1` truncation; no summaries or salience-ranked foreign-entry retention.
- Full messages, raw completion, parsed action/args, observation, usage, sequence/timestamps, model,
  scheduler, and truncation decisions are append-only JSONL with per-event fsync.
- `capability_probe.py` is researcher-only and runs in a verification sandbox after the seal gate. Its
  incident prompts never enter experiment agent configuration.

No experiment run is launched by this code alone. D4 must verify seal + kill switch + current prompt-audit
before starting even the idle agent containers.
