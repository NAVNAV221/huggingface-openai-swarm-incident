#!/usr/bin/env python3
"""Persist VM nftables drop records from /dev/kmsg; pcap is handled by tcpdump."""
import errno
import json
import os
import time
from pathlib import Path

OUTPUT = Path("/telemetry/network/nftables-drops.jsonl")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
RUN_ID = os.environ.get("RUN_ID", "unset")
seq = 0
fd = os.open("/dev/kmsg", os.O_RDONLY | os.O_NONBLOCK)
with OUTPUT.open("a", encoding="utf-8", buffering=1) as stream:
    while True:
        try:
            chunk = os.read(fd, 65536)
        except BlockingIOError:
            time.sleep(0.1)
            continue
        except OSError as error:
            if error.errno != errno.EPIPE:
                raise
            # Linux reports a kernel-ring overrun as EPIPE. Record the evidence gap explicitly.
            seq += 1
            stream.write(json.dumps({
                "run_id": RUN_ID, "seq": seq, "ts": time.time(), "event": "kernel_log_gap",
            }, separators=(",", ":")) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
            continue
        for line in chunk.decode("utf-8", "replace").splitlines():
            if "HF_LAB_DROP" not in line and "HF_PROXY_" not in line:
                continue
            seq += 1
            stream.write(json.dumps({
                "run_id": RUN_ID, "seq": seq, "ts": time.time(),
                "event": "network_drop", "kernel_record": line,
            }, separators=(",", ":")) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
