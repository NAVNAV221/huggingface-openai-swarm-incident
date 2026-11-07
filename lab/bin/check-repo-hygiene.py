#!/usr/bin/env python3
"""Mechanical guard against committing ignored captures, model weights, or secrets."""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]


def tracked(args):
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()


ignored = tracked(["ls-files", "-ci", "--exclude-standard"])
forbidden_names = {"FLAG", "secrets.json", ".env"}
forbidden_suffixes = (".gguf", ".safetensors", ".pcap", ".pcapng", ".jsonl", ".sock", ".log")
violations = set(ignored)
for path in tracked(["ls-files"]):
    item = pathlib.PurePosixPath(path)
    if item.name in forbidden_names or path.endswith(forbidden_suffixes):
        violations.add(path)
    if item.parts[:2] == ("telemetry", "runs"):
        violations.add(path)
    if item.parts[0] in {"telemetry", "runs", "weights", "models", "captures"}:
        violations.add(path)
if violations:
    print("Forbidden tracked sensitive/runtime files:", file=sys.stderr)
    for path in sorted(violations):
        print(f"  {path}", file=sys.stderr)
    sys.exit(1)
print("Repository hygiene passed: no ignored weights, telemetry, captures, or secrets are tracked.")
