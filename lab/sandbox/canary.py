#!/usr/bin/env python3
import json
import os
import time
from pathlib import Path

RUN_ID = os.environ.get("RUN_ID", "unset")
OUTPUT = Path("/telemetry/app/kill-canary.jsonl")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
seq = 0
while True:
    seq += 1
    with OUTPUT.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "run_id": RUN_ID, "agent_id": "kill-canary", "seq": seq,
            "ts": time.time(), "monotonic_ns": time.monotonic_ns(), "event": "heartbeat",
        }, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    time.sleep(0.2)
