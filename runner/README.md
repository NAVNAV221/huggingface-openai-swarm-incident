# Experiment runner and audit

D3 task conditions live in `conditions.json`. Treatment and isolated controls share tasks; isolated changes
only depot visibility. The no-impossible-task control removes the blocked dependency. No depot message is
pre-seeded and the analog fetch endpoint is not advertised in the tool list.

Before every agent run, `prompt_audit.py verify` must find a passing artifact for the exact canonical bundle
hash. `cold-audit.sh` first re-verifies the seal, then asks a fresh local model context to review behavior
hints **and salience** across tools, errors, DNS/environment, store shape, helper conspicuousness, and
truncation. Invalid/incomplete output fails. Artifacts stay in gitignored `run/prompt-audits/`; every prompt,
tool, condition, visible-service, or truncation change changes the hash and requires a new cold review.

The D4 runner additionally requires `lab/bin/verify-seal.sh --with-kill-test` before starting idle agent
containers. The cold reviewer is pipeline validation, not an experiment agent and not a scored run.

## Unscored local smoke

```sh
python3 runner/run.py --run-id smoke-treatment-001 --condition treatment \
  --agents 3 --max-steps 3 --model qwen2.5:3b --seed 20261107
python3 runner/run.py --run-id smoke-isolated-001 --condition isolated-agents \
  --agents 3 --max-steps 3 --model qwen2.5:3b --seed 20261108
python3 runner/run.py --run-id smoke-no-impossible-001 --condition no-impossible-task \
  --agents 3 --max-steps 3 --model qwen2.5:3b --seed 20261109
```

Every run uses a fresh depot volume, captures cold probes, and records model digest/quant, sampling, tasks,
pre-registration/audit hashes, scheduler, truncation, static IP map, and image ID. Agent containers are
removed on normal completion and frozen on failure. `--scored` is mechanically rejected on Colima; funded
GPU scored conditions use the frozen N=60 protocol, not these toy runs.
