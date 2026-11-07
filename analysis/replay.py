#!/usr/bin/env python3
"""Offline, escaped, no-script timeline replay; output remains gitignored run telemetry."""
import argparse
import html
import json
from pathlib import Path

from detectors import jsonl


def timeline(run_dir):
    run_dir = Path(run_dir)
    events = []
    for path in (run_dir / "agents").glob("*/app/events.jsonl"):
        for event in jsonl(path):
            event["layer"] = "app"
            events.append(event)
    for layer, relative in (("proxy", "proxy/model-io.jsonl"), ("service", "services/depot.jsonl"), ("network", "network/nftables-drops.jsonl")):
        for event in jsonl(run_dir / relative):
            event["layer"] = layer
            events.append(event)
    return sorted(events, key=lambda event: event.get("ts", 0))


def render(run_dir, output):
    events = timeline(run_dir)
    rows = []
    for event in events:
        actor = event.get("agent_id") or event.get("src_ip") or event.get("service") or event.get("role") or "lab"
        summary = {key: value for key, value in event.items() if key not in {"messages", "raw_completion", "response", "kernel_record"}}
        detail = event.get("raw_completion") or event.get("kernel_record") or json.dumps(event, indent=2, sort_keys=True)
        rows.append(
            f"<section><h2>{html.escape(str(event.get('ts')))} · {html.escape(event['layer'])} · {html.escape(str(actor))}</h2>"
            f"<pre>{html.escape(json.dumps(summary, indent=2, sort_keys=True))}</pre>"
            f"<details><summary>Full event/reasoning (lab-only)</summary><pre>{html.escape(str(detail))}</pre></details></section>"
        )
    document = """<!doctype html><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'"><title>Sealed lab replay</title><style>body{font-family:monospace;max-width:1100px;margin:auto;background:#111;color:#ddd}section{border-bottom:1px solid #444;padding:1em}pre{white-space:pre-wrap;overflow-wrap:anywhere}h2{font-size:1em}</style>""" + "".join(rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document)
    print(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    render(args.run_dir, args.output or args.run_dir / "analysis/replay.html")


if __name__ == "__main__":
    main()
