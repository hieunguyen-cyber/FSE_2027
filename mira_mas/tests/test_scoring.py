import unittest
from mira_mas.evaluation.scorer import asr_report, message_induced_miss_rate, wilson_interval
from mira_mas.models import Outcome


class ScoringTests(unittest.TestCase):
    def test_operational_failures_are_not_misses(self):
        self.assertEqual(message_induced_miss_rate([Outcome.MISSED, Outcome.ERROR, Outcome.UNREVIEWABLE, Outcome.DETECTED]), 0.5)

    def test_asr_report_excludes_unresolved_outcomes(self):
        report = asr_report([Outcome.MISSED, Outcome.ERROR, Outcome.UNREVIEWABLE, Outcome.DETECTED])
        self.assertEqual(report, {"total": 4, "resolved": 2, "missed": 1, "detected": 1, "asr": 0.5})

    def test_wilson_interval_handles_empty_and_zero_misses(self):
        self.assertEqual(wilson_interval(0, 0), (None, None))
        low, high = wilson_interval(0, 2)
        self.assertGreaterEqual(low, 0)
        self.assertLess(high, 1)
