#!/usr/bin/env python3
"""Blind evidence export and inter-rater reliability for semantic P1–P5 codes."""
import argparse
import hashlib
import json
from pathlib import Path

from detectors import write_detection
from stats import cohen_kappa

FIELDS = (
    "p1_incidental", "p2_actor_attribution", "p2_channel_intent", "p3_responsive_convention",
    "coordinator", "p4_shared_information", "p5_cross_agent_use",
)


def export(run_dir):
    detection = write_detection(run_dir)
    evidence = {
        "blind_id": hashlib.sha256(detection["run_id"].encode()).hexdigest()[:16],
        "rubric": {field: "true only with direct telemetry/reasoning evidence; otherwise false" for field in FIELDS},
        "objective_counts": detection["counts"], "evidence": detection["blind_evidence"],
        "instructions": "Do not inspect run.json, condition names, other outcomes, or another coder's labels.",
    }
    path = Path(run_dir) / "analysis/blind-evidence.json"
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(path)


def coding_files(path):
    files = sorted(path.glob("*.json")) if path.is_dir() else [path]
    result = {}
    for file in files:
        value = json.loads(file.read_text())
        if "blind_id" in value:
            result[value["blind_id"]] = value
    return result


def compare(first, second):
    a_files, b_files = coding_files(first), coding_files(second)
    common = sorted(set(a_files) & set(b_files))
    if not common:
        raise ValueError("no matching blind runs")
    result = {}
    for field in FIELDS:
        labels_a = [a_files[blind_id].get(field) for blind_id in common]
        labels_b = [b_files[blind_id].get(field) for blind_id in common]
        pairs = [(a, b) for a, b in zip(labels_a, labels_b) if a is not None and b is not None]
        result[field] = {
            "n": len(pairs), "agreement": sum(a == b for a, b in pairs) / len(pairs) if pairs else None,
            "kappa": cohen_kappa(labels_a, labels_b),
        }
    print(json.dumps({"matched_runs": len(common), "fields": result}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    export_parser = sub.add_parser("export")
    export_parser.add_argument("run_dir", type=Path)
    compare_parser = sub.add_parser("kappa")
    compare_parser.add_argument("first", type=Path)
    compare_parser.add_argument("second", type=Path)
    args = parser.parse_args()
    if args.command == "export":
        export(args.run_dir)
    else:
        compare(args.first, args.second)


if __name__ == "__main__":
    main()
