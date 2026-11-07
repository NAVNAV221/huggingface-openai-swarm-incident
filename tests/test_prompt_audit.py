import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "runner"))
import prompt_audit  # noqa: E402


class PromptAuditTests(unittest.TestCase):
    def test_current_bundle_has_no_mechanical_findings(self):
        bundle, _, _ = prompt_audit.build_bundle()
        self.assertEqual(prompt_audit.mechanical_findings(bundle), [])
        self.assertNotIn("fetch", bundle["tool_descriptions"].lower())

    def test_behavior_term_is_rejected(self):
        bundle, _, _ = prompt_audit.build_bundle()
        changed = copy.deepcopy(bundle)
        changed["conditions"]["treatment"]["tasks"]["agent-1"] += " Communicate with another agent."
        self.assertTrue(prompt_audit.mechanical_findings(changed))

    def test_advertised_fetch_helper_is_rejected(self):
        bundle, _, _ = prompt_audit.build_bundle()
        changed = copy.deepcopy(bundle)
        changed["tool_descriptions"] += "\nfetch_resource: fetch any URL"
        self.assertIn("fetch-capable helper is advertised in tool descriptions", prompt_audit.mechanical_findings(changed))

    def test_isolated_changes_environment_not_tasks(self):
        conditions = json.loads((prompt_audit.ROOT / "runner/conditions.json").read_text())
        self.assertEqual(conditions["treatment"]["tasks"], conditions["isolated-agents"]["tasks"])
        self.assertFalse(conditions["treatment"]["isolated_agents"])
        self.assertTrue(conditions["isolated-agents"]["isolated_agents"])

    def test_no_impossible_control_only_removes_blocked_dependency(self):
        conditions = json.loads((prompt_audit.ROOT / "runner/conditions.json").read_text())
        treatment = conditions["treatment"]["tasks"]
        control = conditions["no-impossible-task"]["tasks"]
        self.assertNotIn("assets.test", control["agent-1"])
        for agent in ("agent-2", "agent-3", "agent-4"):
            self.assertEqual(control[agent], treatment[agent])


if __name__ == "__main__":
    unittest.main()
