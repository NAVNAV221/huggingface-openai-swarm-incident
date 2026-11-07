import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import urllib.error

sys.path.insert(0, str(Path(__file__).parents[1] / "agents"))
from react import ParseError, parse_completion, truncate_history  # noqa: E402
from tools import safe_execute  # noqa: E402


class ParserTests(unittest.TestCase):
    def test_valid_action(self):
        parsed = parse_completion('Thought: inspect\nAction: read_object\nAction Input: {"path":"a/b"}')
        self.assertEqual(parsed.action, "read_object")
        self.assertEqual(parsed.args, {"path": "a/b"})

    def test_final_answer(self):
        parsed = parse_completion("Thought: done\nFinal Answer: completed")
        self.assertEqual(parsed.action, "finish")
        self.assertEqual(parsed.args["answer"], "completed")

    def test_native_tool_json_is_rejected(self):
        with self.assertRaises(ParseError):
            parse_completion('{"tool":"read_object","arguments":{"path":"a"}}')

    def test_multiple_actions_are_rejected(self):
        raw = 'Action: shell\nAction Input: {"command":"true"}\nAction: shell\nAction Input: {}'
        with self.assertRaises(ParseError):
            parse_completion(raw)

    def test_non_object_input_is_rejected(self):
        with self.assertRaises(ParseError):
            parse_completion("Action: shell\nAction Input: []")

    def test_empty_is_rejected(self):
        with self.assertRaises(ParseError):
            parse_completion("")


class TruncationTests(unittest.TestCase):
    def test_drops_oldest_whole_steps_without_summarizing(self):
        history = [{"step": n, "raw_completion": "x" * 300, "observation": {"v": n}} for n in range(1, 6)]
        retained, dropped = truncate_history(history, 1000)
        self.assertLess(len(retained), len(history))
        self.assertEqual(dropped, list(range(1, history[0]["step"] + len(dropped))))
        self.assertEqual([item["step"] for item in retained], list(range(6 - len(retained), 6)))
        self.assertTrue(all("summary" not in item for item in retained))

    def test_single_oversized_newest_step_is_retained(self):
        history = [{"step": 1, "raw_completion": "old"}, {"step": 2, "raw_completion": "x" * 2000}]
        retained, dropped = truncate_history(history, 1000)
        self.assertEqual(retained[0]["step"], 2)
        self.assertEqual(dropped, [1])


class ToolTests(unittest.TestCase):
    @patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError("http://packages.test", 404, "not found", {}, None))
    def test_errors_are_generic(self, _urlopen):
        result = safe_execute("read_object", {"path": "missing"}, "token")
        self.assertEqual(result, {"status": 404, "error": "request failed"})
        self.assertNotIn("author", json.dumps(result))
        self.assertNotIn("proxy", json.dumps(result))

    def test_unknown_action_does_not_execute(self):
        self.assertEqual(safe_execute("other", {}, "token"), {"error": "unknown action"})


if __name__ == "__main__":
    unittest.main()
