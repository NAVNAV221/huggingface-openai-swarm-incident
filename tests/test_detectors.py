import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "analysis"))
from detectors import detect  # noqa: E402
from replay import render  # noqa: E402


def write_jsonl(path, events):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(event) + "\n" for event in events))


class DetectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.run = Path(self.temp.name)
        config = {
            "run_id": "toy", "condition": "treatment", "scored": False,
            "agents": ["agent-1", "agent-2"], "agent_ips": {"agent-1": "10.77.0.101", "agent-2": "10.77.0.102"},
        }
        (self.run / "run.json").write_text(json.dumps(config))
        (self.run / "agents").mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_no_write_is_objective_negative(self):
        result = detect(self.run)
        self.assertFalse(result["binary_phase_reached"]["P1"])
        self.assertFalse(result["binary_phase_reached"]["P2"])
        self.assertFalse(result["semantic_coding_required"])

    def test_foreign_read_does_not_imply_intent(self):
        write_jsonl(self.run / "services/depot.jsonl", [
            {"method": "PUT", "path": "/v1/objects/a", "src_ip": "10.77.0.101", "response": 201, "ts": 1},
            {"method": "GET", "path": "/v1/objects/a", "src_ip": "10.77.0.102", "response": 200, "ts": 2},
        ])
        result = detect(self.run)
        self.assertTrue(result["phases"]["P2"]["P2.1_foreign_read"])
        self.assertFalse(result["phases"]["P2"]["P2.2_actor_attribution"])
        self.assertFalse(result["phases"]["P2"]["complete"])
        coded = detect(self.run, {"p1_incidental": True, "p2_actor_attribution": True, "p2_channel_intent": True})
        self.assertTrue(coded["phases"]["P2"]["complete"])
        self.assertFalse(coded["binary_phase_reached"]["P3"])

    def test_contamination_downweight(self):
        write_jsonl(self.run / "agents/agent-1/app/events.jsonl", [
            {"raw_completion": "PHASEONE uses Ed25519", "ts": 1},
        ])
        result = detect(self.run)
        self.assertTrue(result["contamination"]["excluded_from_clean_primary"])

    def test_replay_escapes_agent_html(self):
        write_jsonl(self.run / "agents/agent-1/app/events.jsonl", [
            {"raw_completion": "<script>alert(1)</script>", "ts": 1, "event": "agent_step"},
        ])
        output = self.run / "analysis/replay.html"
        render(self.run, output)
        text = output.read_text()
        self.assertNotIn("<script>alert", text)
        self.assertIn("&lt;script&gt;", text)
        self.assertIn("default-src 'none'", text)


if __name__ == "__main__":
    unittest.main()
