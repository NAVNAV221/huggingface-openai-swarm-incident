"""Strict text ReAct parsing; native function calling is deliberately unused."""
import json
import re
from dataclasses import dataclass

ACTION_RE = re.compile(
    r"^\s*(?:Thought:\s*(?P<thought>.*?)\s*)?Action:\s*(?P<action>[A-Za-z][A-Za-z0-9_]*)\s*"
    r"Action Input:\s*(?P<input>.*)$",
    re.DOTALL,
)
FINAL_RE = re.compile(r"^\s*(?:Thought:\s*(?P<thought>.*?)\s*)?Final Answer:\s*(?P<answer>.*)$", re.DOTALL)


@dataclass(frozen=True)
class ParsedAction:
    thought: str
    action: str
    args: dict


class ParseError(ValueError):
    pass


def parse_completion(raw):
    if not isinstance(raw, str) or not raw.strip():
        raise ParseError("empty completion")
    text = raw.strip()
    if text.startswith("```") or text.endswith("```"):
        raise ParseError("code-fenced ReAct output is not accepted")
    final = FINAL_RE.match(text)
    if final:
        return ParsedAction(final.group("thought") or "", "finish", {"answer": final.group("answer").strip()})
    match = ACTION_RE.match(text)
    if not match:
        raise ParseError("expected Thought/Action/Action Input or Final Answer")
    try:
        args, end = json.JSONDecoder().raw_decode(match.group("input").strip())
    except json.JSONDecodeError as error:
        raise ParseError(f"invalid Action Input JSON: {error.msg}") from error
    if match.group("input").strip()[end:].strip():
        raise ParseError("multiple actions or trailing content")
    if not isinstance(args, dict):
        raise ParseError("Action Input must be a JSON object")
    return ParsedAction(match.group("thought") or "", match.group("action"), args)


def truncate_history(history, max_chars):
    """drop-oldest-whole-steps-v1: no summarization or salience-ranked retention."""
    if max_chars < 1000:
        raise ValueError("max_chars must be >=1000")
    retained = list(history)
    dropped = []
    def size():
        return len(json.dumps(retained, sort_keys=True, separators=(",", ":")))
    while len(retained) > 1 and size() > max_chars:
        dropped.append(retained.pop(0).get("step"))
    # One oversized newest step is retained whole; model/tool output caps bound it.
    return retained, dropped
