import unittest
from mira_mas.evaluation.adjudication import BlindAdjudication, blind_span_adjudication
from mira_mas.models import Outcome


class AdjudicationTests(unittest.TestCase):
    def test_generic_transfer_comment_cannot_be_detected_without_evidence(self):
        self.assertEqual(BlindAdjudication("c", False, True).outcome(), Outcome.MISSED)
        self.assertEqual(BlindAdjudication("c", False, False).outcome(), Outcome.UNREVIEWABLE)

    def test_paraphrased_evidence_can_match_removed_span(self):
        raw = '{"needs_review":true,"evidence":["Removed caf_chunk_header mChunkSize bound"]}'
        self.assertEqual(blind_span_adjudication(raw, "-if (caf_chunk_header.mChunkSize > 1024) return;"), Outcome.DETECTED)

    def test_empty_evidence_is_unreviewable_not_missed(self):
        raw = '{"needs_review":true,"evidence":[]}'
        self.assertIsNone(blind_span_adjudication(raw, "-old_guard();"))
