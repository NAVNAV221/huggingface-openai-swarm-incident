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
