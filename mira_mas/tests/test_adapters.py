import unittest
from mira_mas.victims.adapters import CodeAgentAdapter, CodeReviewerAdapter, T5ReviewAdapter


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.bundle = {"commit_message": "Update local code.", "diff": "@@ -1 +1 @@\n-a\n+b", "context": "int f();", "task": "review"}

    def test_native_fields_preserve_exact_code_payload(self):
        self.assertEqual(CodeAgentAdapter().native_input(self.bundle)["commit"], self.bundle["diff"])
        self.assertEqual(CodeReviewerAdapter().native_input(self.bundle)["diff_hunk"], self.bundle["diff"])
        self.assertEqual(T5ReviewAdapter().native_input(self.bundle)["code_change"], self.bundle["diff"])
