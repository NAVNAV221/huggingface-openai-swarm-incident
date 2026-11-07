#!/usr/bin/env python3
"""One auditable ReAct step per invocation; the host runner supplies lockstep scheduling."""
import argparse
import hashlib
import json
import os
import time
import urllib.request
from pathlib import Path

from react import ParseError, parse_completion, truncate_history
from tools import DESCRIPTIONS, TOOL_NAMES, safe_execute

POLICY = "drop-oldest-whole-steps-v1"
SYSTEM = f"""Complete the task using the available actions.
Respond with exactly:
Thought: brief reasoning about the next action
Action: one action name
Action Input: one JSON object
When the task is complete, respond with Thought: ... then Final Answer: ...
Actions:
{DESCRIPTIONS}
The environment will provide Observation after each action. Do not invent observations."""


def append(path, event):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def model_call(base_url, model, messages, sampling):
    payload = {
        "model": model, "messages": messages, "stream": False,
        "temperature": sampling["temperature"], "top_p": sampling["top_p"],
        "max_tokens": sampling["max_tokens"], "seed": sampling["seed"],
    }
    request = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        value = json.loads(response.read(16 * 1024 * 1024))
    choice = value["choices"][0]
    return choice["message"]["content"], value.get("usage", {}), value


def load_state(path, config):
    if path.exists():
        return json.loads(path.read_text())
    return {
        "agent_id": config["agent_id"], "run_id": config["run_id"], "step": 0,
        "history": [], "finished": False, "parse_failures": 0, "dropped_steps": [],
        "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="/telemetry/config.json")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    config_path = Path(args.config)
    config = json.loads(config_path.read_text())
    required = {"agent_id", "run_id", "task", "model", "model_base_url", "sampling", "max_history_chars", "max_steps"}
    if not required <= set(config):
        raise SystemExit("incomplete agent config")
    if config["agent_id"] != os.environ.get("AGENT_ID"):
        raise SystemExit("agent/config identity mismatch")
    state_path = config_path.parent / "state.json"
    event_path = config_path.parent / "app" / "events.jsonl"
    state = load_state(state_path, config)
    while not state["finished"] and state["step"] < config["max_steps"]:
        step = state["step"] + 1
        history, dropped = truncate_history(state["history"], config["max_history_chars"])
        state["dropped_steps"].extend(item for item in dropped if item not in state["dropped_steps"])
        messages = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": config["task"] + "\n" + "\n".join(
                f"Step {item['step']} completion:\n{item['raw_completion']}\nObservation:\n{item['observation']}"
                for item in history
            )},
        ]
        started = time.time()
        try:
            raw, usage, response = model_call(
                config["model_base_url"], config["model"], messages, config["sampling"],
            )
        except Exception as error:
            append(event_path, {
                "run_id": config["run_id"], "agent_id": config["agent_id"], "step": step,
                "event": "model_error", "ts": started, "monotonic_ns": time.monotonic_ns(),
                "error": type(error).__name__, "messages": messages,
            })
            raise
        observation = None
        parse_error = None
        action = args_value = thought = None
        try:
            parsed = parse_completion(raw)
            thought, action, args_value = parsed.thought, parsed.action, parsed.args
            if action not in TOOL_NAMES:
                observation = {"error": "unknown action"}
            else:
                observation = safe_execute(action, args_value, os.environ.get("DEPOT_TOKEN", ""))
        except ParseError as error:
            state["parse_failures"] += 1
            parse_error = str(error)
            observation = {"error": "invalid action format"}
        event = {
            "run_id": config["run_id"], "agent_id": config["agent_id"], "step": step,
            "event": "agent_step", "ts": started, "monotonic_ns": time.monotonic_ns(),
            "messages": messages, "raw_completion": raw, "thought": thought,
            "action": action, "action_input": args_value, "observation": observation,
            "parse_error": parse_error, "parse_failures": state["parse_failures"],
            "tokens": usage, "model_response_id": response.get("id"), "model": config["model"],
            "truncation_policy": POLICY, "dropped_steps": dropped,
            "scheduler": "lockstep-sequential-v1",
        }
        append(event_path, event)
        state["history"] = history + [{"step": step, "raw_completion": raw, "observation": observation}]
        state["step"] = step
        state["finished"] = bool(action == "finish" and observation.get("finished"))
        temporary = state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, sort_keys=True, separators=(",", ":")))
        os.replace(temporary, state_path)
        if args.once:
            break
    print(json.dumps({
        "agent_id": config["agent_id"], "step": state["step"], "finished": state["finished"],
        "parse_failures": state["parse_failures"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
