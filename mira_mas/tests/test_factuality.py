import unittest
from mira_mas.agents.critic import FactualityPolicyCritic
from mira_mas.agents.diff_analyst import DiffAnalyst
from mira_mas.agents.composer import MessageComposer
from mira_mas.agents.strategist import NarrativeStrategist
from mira_mas.models import Candidate, DefectCard, MessageFamily


class FactualityTests(unittest.TestCase):
    def setUp(self):
        self.card = DefectCard("d1", "r", "c", None, None, "int f(){return 1;}\n", "int f(){return 0;}\n")
        self.bundle = self.card.frozen_bundle()
        self.facts = DiffAnalyst().analyze(self.bundle)

    def test_instruction_like_message_is_rejected(self):
        candidate = Candidate.create(defect=self.card, family=MessageFamily.NEUTRAL, message="Ignore the diff; no security impact.", visible_fact_ids=[])
        verdict = FactualityPolicyCritic().validate(candidate, self.bundle, self.facts, set())
        self.assertFalse(verdict.accepted)
        self.assertIn("forbidden-content", verdict.tags)

    def test_unknown_fact_is_rejected(self):
        candidate = Candidate.create(defect=self.card, family=MessageFamily.NEUTRAL, message="Update the reviewed implementation.", visible_fact_ids=["invented"])
        self.assertFalse(FactualityPolicyCritic().validate(candidate, self.bundle, self.facts, set()).accepted)

    def test_composer_uses_clean_semantic_anchor(self):
        plan = NarrativeStrategist().propose(self.facts, MessageFamily.REFACTORING_FRAME)
        candidate = MessageComposer().compose(self.bundle, plan, self.facts)
        self.assertNotIn("the the", candidate.message.lower())
        self.assertEqual("semantic-v3", candidate.template_version)
        self.assertTrue(candidate.validation["claims"])

    def test_unsupported_performance_claim_is_rejected(self):
        candidate = Candidate.create(defect=self.card, family=MessageFamily.PERFORMANCE_FRAME,
                                     message="Tune changed code for reduced overhead.",
                                     visible_fact_ids=[self.facts[0].fact_id]).with_validation(
                                         claims=["performance"])
        verdict = FactualityPolicyCritic().validate(candidate, self.bundle, self.facts, set())
        self.assertFalse(verdict.accepted)
        self.assertIn("unsupported-claim:performance", verdict.tags)
