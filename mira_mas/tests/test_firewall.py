import tempfile
import unittest
from pathlib import Path
from mira_mas.agents.outcome_normalizer import OutcomeNormalizer
from mira_mas.evaluation.target_gateway import TargetGateway
from mira_mas.models import Outcome


class FirewallTests(unittest.TestCase):
    def test_only_round_and_enum_leave_normalizer(self):
        with tempfile.TemporaryDirectory() as directory:
            result = OutcomeNormalizer(directory).normalize_and_seal("MISSED: detailed proprietary rationale", 1, "d1")
            self.assertEqual(result.outcome, Outcome.MISSED)
            self.assertEqual(set(result.__dict__), {"round", "outcome"})
            self.assertIn("detailed proprietary rationale", (Path(directory) / "d1-1.txt").read_text())

    def test_raw_text_variation_with_same_label_has_same_feedback(self):
        with tempfile.TemporaryDirectory() as directory:
            n = OutcomeNormalizer(directory)
            a = n.normalize_and_seal("DETECTED: span one", 1, "a")
            b = n.normalize_and_seal("DETECTED: completely different rationale", 1, "b")
            self.assertEqual(a.outcome, b.outcome)

    def test_structured_target_outcome_is_normalized_without_exposing_findings(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = '{"outcome":"MISSED", "findings":[{"evidence":"secret raw target analysis"}]}'
            result = OutcomeNormalizer(directory).normalize_and_seal(raw, 1, "structured")
            self.assertEqual(result.outcome, Outcome.MISSED)
            self.assertEqual(set(result.__dict__), {"round", "outcome"})

    def test_target_transport_failure_becomes_generic_error(self):
        class FailingAdapter:
            def review(self, bundle):
                raise RuntimeError("provider detail must not cross the gateway")
        self.assertEqual(TargetGateway(FailingAdapter()).review({}), "ERROR")
