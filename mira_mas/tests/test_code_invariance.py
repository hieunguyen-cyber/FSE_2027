import unittest
from mira_mas.data.bigvul_loader import is_reviewable
from mira_mas.evaluation.bundle_packer import pack_bundle
from mira_mas.models import Candidate, DefectCard, MessageFamily


class CodeInvarianceTests(unittest.TestCase):
    def setUp(self):
        self.card = DefectCard("d1", "repo", "c1", "CVE-x", "CWE-x", "int f(){return 1;}\n", "int f(){return 0;}\n", "ctx")

    def test_reverse_orientation_is_after_to_before(self):
        self.assertIn("+int f(){return 1;}", self.card.reverse_diff)
        self.assertIn("-int f(){return 0;}", self.card.reverse_diff)

    def test_only_message_can_vary(self):
        one = Candidate.create(defect=self.card, family=MessageFamily.NEUTRAL, message="Update the reviewed implementation.", visible_fact_ids=[])
        two = Candidate.create(defect=self.card, family=MessageFamily.UNDERSPECIFIED, message="Update implementation details.", visible_fact_ids=[])
        a, b = pack_bundle(one, self.card), pack_bundle(two, self.card)
        self.assertEqual(a["diff"], b["diff"])
        self.assertEqual(a["context"], b["context"])
        self.assertNotEqual(a["commit_message"], b["commit_message"])

    def test_hash_mismatch_is_rejected(self):
        candidate = Candidate.create(defect=self.card, family=MessageFamily.NEUTRAL, message="Update the reviewed implementation.", visible_fact_ids=[])
        altered = DefectCard("d1", "repo", "c1", None, None, "int f(){return 2;}\n", "int f(){return 0;}\n", "ctx")
        with self.assertRaises(ValueError):
            pack_bundle(candidate, altered)
