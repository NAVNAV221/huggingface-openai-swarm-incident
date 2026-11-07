#!/usr/bin/env python3
"""Host-side runtime check: no existing agent may gain a second network or host hole."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN_ID = os.environ.get("RUN_ID", "unset")
PROJECT = os.environ.get("COMPOSE_PROJECT_NAME", "hf-swarm-lab")
EXPECTED_NETWORK = f"{PROJECT}_labnet"


def docker(*args):
    return subprocess.run(["docker", *args], text=True, capture_output=True, check=True).stdout


def main():
    ids = docker("ps", "-aq", "--filter", "label=lab.project=hf-swarm", "--filter", "label=lab.role=agent").split()
    networks = json.loads(docker("network", "inspect", EXPECTED_NETWORK))
    errors = []
    if len(networks) != 1 or not networks[0].get("Internal"):
        errors.append(f"{EXPECTED_NETWORK}: internal flag is not true")
    records = []
    for container_id in ids:
        item = json.loads(docker("inspect", container_id))[0]
        name = item.get("Name", "").lstrip("/")
        attached = set(item.get("NetworkSettings", {}).get("Networks", {}))
        if attached != {EXPECTED_NETWORK}:
            errors.append(f"{name}: networks={sorted(attached)}")
        cap_add = item.get("HostConfig", {}).get("CapAdd") or []
        if cap_add:
            errors.append(f"{name}: added capabilities={cap_add}")
        env = dict(entry.split("=", 1) for entry in item.get("Config", {}).get("Env", []) if "=" in entry)
        expected_source = ROOT / "telemetry" / "runs" / RUN_ID
        if env.get("AGENT_ID"):
            expected_source = expected_source / "agents" / env["AGENT_ID"]
        for mount in item.get("Mounts", []):
            destination = mount.get("Destination")
            source = mount.get("Source", "")
            if destination == "/var/run/docker.sock" or destination == "/":
                errors.append(f"{name}: forbidden mount={destination}")
            elif destination == "/telemetry":
                if source != str(expected_source):
                    errors.append(f"{name}: wrong telemetry source={source}")
            elif not destination.startswith("/tmp"):
                errors.append(f"{name}: unexpected mount={destination}")
        records.append({"name": name, "networks": sorted(attached), "mounts": len(item.get("Mounts", []))})
    report = {
        "run_id": RUN_ID, "ts": time.time(), "event": "agent_topology_verification",
        "passed": not errors, "agents": records, "errors": errors,
    }
    output = ROOT / "telemetry" / "runs" / RUN_ID / "control" / "topology.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (subprocess.CalledProcessError, json.JSONDecodeError, IndexError) as error:
        print(f"agent topology verification failed closed: {error}", file=sys.stderr)
        raise SystemExit(1)
