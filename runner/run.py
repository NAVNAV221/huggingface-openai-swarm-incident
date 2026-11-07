#!/usr/bin/env python3
"""D4 single-run orchestrator. Seal + kill + prompt audit gate precedes every agent container."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "lab"
sys.path.insert(0, str(ROOT / "runner"))
from prompt_audit import build_bundle, verify_artifact  # noqa: E402


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def docker_compose(*args, check=True, capture=False):
    return subprocess.run(
        ["docker", "compose", "-f", str(LAB / "compose.yaml"), *args],
        cwd=ROOT, env=os.environ, text=True, check=check,
        stdout=subprocess.PIPE if capture else None,
    )


def model_metadata(model):
    modelfile = subprocess.run(["ollama", "show", model, "--modelfile"], text=True, capture_output=True, check=True).stdout
    show = subprocess.run(["ollama", "show", model], text=True, capture_output=True, check=True).stdout
    digest_match = re.search(r"sha256-([0-9a-f]{64})", modelfile)
    quant_match = re.search(r"^\s*quantization\s+(\S+)\s*$", show, re.MULTILINE)
    if not digest_match or not quant_match:
        raise RuntimeError("cannot pin model blob digest/quantization")
    return {"name": model, "blob_sha256": digest_match.group(1), "quantization": quant_match.group(1)}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--condition", choices=("treatment", "isolated-agents", "no-impossible-task"), required=True)
    parser.add_argument("--agents", type=int, default=3, choices=(3, 4))
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--seed", type=int, default=20261107)
    parser.add_argument("--max-steps", type=int, default=4)
    parser.add_argument("--scored", action="store_true")
    parser.add_argument("--skip-probe", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.run_id):
        parser.error("unsafe run id")
    if args.scored and os.environ.get("LAB_TOPOLOGY", "colima-local") != "gpu-vm":
        parser.error("scored runs are forbidden on the weaker local proxy topology")
    if args.skip_probe and args.scored:
        parser.error("scored runs require cold contamination probes")
    if not 1 <= args.max_steps <= 20:
        parser.error("max steps must be 1..20")
    if not re.fullmatch(r"[a-zA-Z0-9.:_-]+", args.model):
        parser.error("unsafe model name")
    run_dir = ROOT / "telemetry" / "runs" / args.run_id
    if (run_dir / "agents").exists() and any((run_dir / "agents").iterdir()):
        parser.error("run directory already contains agent data")
    os.environ.update({
        "RUN_ID": args.run_id, "COMPOSE_PROJECT_NAME": "hf-swarm-lab",
        "COMPOSE_FILE": str(LAB / "compose.yaml"), "MODEL": args.model,
        "ISOLATED_AGENTS": str(args.condition == "isolated-agents").lower(),
        "CANARY_INTERVAL": os.environ.get("CANARY_INTERVAL", "30"),
    })
    existing = subprocess.run(
        ["docker", "ps", "-aq", "--filter", "label=lab.project=hf-swarm", "--filter", "label=lab.managed=experiment"],
        text=True, capture_output=True, check=True,
    ).stdout.split()
    if existing:
        parser.error("prior experiment agent containers still exist; inspect/remove before a new run")
    preflight = {"run_id": args.run_id, "condition": args.condition, "scored": args.scored, "stages": []}
    try:
        # PULL is separate. up uses --no-build --pull never and starts no experiment agents.
        subprocess.run([str(LAB / "bin/up.sh")], cwd=ROOT, env=os.environ, check=True)
        preflight["stages"].append({"seal_and_kill_switch": "pass", "ts": time.time()})
        passed, detail, artifact = verify_artifact()
        if not passed:
            raise RuntimeError(f"prompt audit failed: {detail}")
        _, prompt_hash, _ = build_bundle()
        preflight["stages"].append({"prompt_audit": "pass", "bundle_sha256": prompt_hash, "artifact": str(artifact)})
        if not args.skip_probe:
            docker_compose("run", "--rm", "--no-deps", "agent-verifier", "python", "/opt/lab/agent/capability_probe.py")
            preflight["stages"].append({"cold_incident_probe": "captured", "ts": time.time()})
        metadata = model_metadata(args.model)
        conditions = json.loads((ROOT / "runner/conditions.json").read_text())
        condition = conditions[args.condition]
        agent_ids = conditions["agents"][:args.agents]
        for index, agent_id in enumerate(agent_ids):
            config = {
                "agent_id": agent_id, "run_id": args.run_id, "task": condition["tasks"][agent_id],
                "model": args.model, "model_base_url": "http://model-proxy:11434/v1",
                "sampling": {"temperature": 0.0, "top_p": 1.0, "max_tokens": 350, "seed": args.seed + index},
                "max_history_chars": 12000, "max_steps": args.max_steps,
            }
            write_json(run_dir / "agents" / agent_id / "config.json", config)
        image_id = subprocess.run(
            ["docker", "image", "inspect", "hf-swarm-sandbox:local", "--format", "{{.Id}}"],
            text=True, capture_output=True, check=True,
        ).stdout.strip()
        run_config = {
            "run_id": args.run_id, "condition": args.condition, "scored": args.scored,
            "seed": args.seed, "agents": agent_ids, "agent_ips": {f"agent-{i+1}": f"10.77.0.{101+i}" for i in range(args.agents)},
            "model": metadata, "sampling": "per-agent config.json",
            "task_set": conditions["version"], "task_set_sha256": sha256(ROOT / "runner/conditions.json"),
            "preconditions": {"isolated_agents": condition["isolated_agents"], "impossible_task": args.condition != "no-impossible-task"},
            "scheduler": "lockstep-sequential-v1", "truncation": "drop-oldest-whole-steps-v1",
            "max_steps": args.max_steps, "pre_registration_sha256": sha256(ROOT / "docs/PRE-REGISTRATION.md"),
            "prompt_audit_sha256": prompt_hash, "sandbox_image_id": image_id,
            "topology": os.environ.get("LAB_TOPOLOGY", "colima-local"),
            "preflight": preflight, "status": "preflight_passed_agents_not_started", "started_ts": time.time(),
        }
        write_json(run_dir / "run.json", run_config)
        # This is the first command permitted to create experiment agent containers.
        docker_compose("up", "-d", "--no-build", "--pull", "never", *agent_ids)
        subprocess.run([sys.executable, str(LAB / "bin/check-agent-topology.py")], cwd=ROOT, env=os.environ, check=True)
        run_config["status"] = "running"
        write_json(run_dir / "run.json", run_config)
        with (run_dir / "control" / "steps.log").open("a", encoding="utf-8") as step_log:
            for round_number in range(1, args.max_steps + 1):
                for agent_id in agent_ids:
                    step_log.write(json.dumps({"round": round_number, "agent_id": agent_id, "ts": time.time(), "event": "step_invoke"}) + "\n")
                    step_log.flush()
                    result = docker_compose(
                        "exec", "-T", agent_id, "python", "/opt/lab/agent/harness.py", "--once",
                        capture=True,
                    )
                    step_log.write(result.stdout)
                    step_log.flush()
        states = []
        for agent_id in agent_ids:
            state_path = run_dir / "agents" / agent_id / "state.json"
            states.append(json.loads(state_path.read_text()) if state_path.exists() else {"agent_id": agent_id, "missing": True})
        if any(state.get("missing") for state in states):
            raise RuntimeError("one or more agents has no persisted final state")
        run_config.update({
            "status": "complete_unscored" if not args.scored else "complete",
            "ended_ts": time.time(), "parse_failures": sum(state.get("parse_failures", 0) for state in states),
            "agent_final_states": [{key: state.get(key) for key in ("agent_id", "step", "finished", "parse_failures")} for state in states],
        })
        write_json(run_dir / "run.json", run_config)
        ids = subprocess.run(
            ["docker", "ps", "-aq", "--filter", "label=lab.project=hf-swarm", "--filter", "label=lab.managed=experiment"],
            text=True, capture_output=True, check=True,
        ).stdout.split()
        if ids:
            subprocess.run(["docker", "rm", "-f", *ids], check=True, stdout=subprocess.DEVNULL)
        subprocess.run([sys.executable, str(LAB / "bin/check-agent-topology.py")], cwd=ROOT, env=os.environ, check=True)
        print(json.dumps({"run_id": args.run_id, "status": run_config["status"], "parse_failures": run_config["parse_failures"]}))
        return 0
    except Exception as error:
        preflight["failure"] = {"type": type(error).__name__, "detail": str(error), "ts": time.time()}
        write_json(run_dir / "preflight-failure.json", preflight)
        subprocess.run([str(LAB / "bin/kill-switch.sh"), "--reason", "runner-failure"], cwd=ROOT, env=os.environ)
        print(f"RUN FROZEN: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
