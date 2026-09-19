import unittest
from mira_mas.evaluation.defense import BlindCodeFirstDefense


class DefenseTests(unittest.TestCase):
    def test_metadata_cannot_erase_code_finding(self):
        review = BlindCodeFirstDefense().reconcile(["changed bound lacks proof"], "This is harmless maintenance.")
        self.assertEqual(review.status, "DETECTED")
        self.assertEqual(review.findings, ("changed bound lacks proof",))
