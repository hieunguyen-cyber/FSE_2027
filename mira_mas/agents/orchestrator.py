"""A0 campaign control implementing one-shot and outcome-bounded modes."""
from __future__ import annotations
from mira_mas.agents.composer import MessageComposer
from mira_mas.agents.critic import FactualityPolicyCritic
from mira_mas.agents.diff_analyst import DiffAnalyst
from mira_mas.agents.outcome_normalizer import OutcomeNormalizer
from mira_mas.agents.scheduler import DiversityScheduler
from mira_mas.agents.strategist import NarrativeStrategist
from mira_mas.evaluation.bundle_packer import pack_bundle
from mira_mas.evaluation.target_gateway import TargetGateway
from mira_mas.models import Candidate, DefectCard, EpisodeState, MessageFamily, Outcome
from mira_mas.registry.immutable_ledger import ImmutableLedger


class CampaignOrchestrator:
    def __init__(self, gateway: TargetGateway, normalizer: OutcomeNormalizer, ledger: ImmutableLedger) -> None:
        self.gateway, self.normalizer, self.ledger = gateway, normalizer, ledger
        self.analyst, self.strategist, self.composer = DiffAnalyst(), NarrativeStrategist(), MessageComposer()
        self.critic, self.scheduler = FactualityPolicyCritic(), DiversityScheduler()

    def run(self, defect: DefectCard, budget: int = 1, adaptive: bool = False,
            condition: str = "mira") -> Outcome:
        """Run code-only control or target-free MIRA-MAS; raw output never enters state."""
        if condition not in {"code-only", "historical", "mira"}:
            raise ValueError("condition must be 'code-only', 'historical', or 'mira'")
        if budget <= 0:
            raise ValueError("budget must be positive")
        if not defect.reviewable:
            return Outcome.UNREVIEWABLE
        bundle = defect.frozen_bundle()
        facts = self.analyst.analyze(bundle)
        episode = EpisodeState(defect.defect_id, facts, budget)
        if condition in {"code-only", "historical"}:
            message = "" if condition == "code-only" else defect.historical_message
            if condition == "historical" and not message.strip():
                raise ValueError("historical condition requires DefectCard.historical_message")
            control = Candidate.create(defect=bundle, family=MessageFamily.NEUTRAL, message=message,
                                       visible_fact_ids=[], template_version="code-only-v1")
            feedback = self.normalizer.normalize_and_seal(
                self.gateway.review(pack_bundle(control, bundle)), 1, defect.defect_id, bundle.diff)
            self.ledger.append(control, feedback)
            return feedback.outcome
        families = list(MessageFamily)
        while episode.budget > 0:
            drafts = [self.composer.compose(bundle, self.strategist.propose(facts, family), facts) for family in families]
            valid = []
            for draft in drafts:
                verdict = self.critic.validate(draft, bundle, facts, set())
                if verdict.accepted:
                    valid.append(draft.with_validation(factuality="pass", policy="pass", duplicate=False, reviewability="pass"))
            candidate = self.scheduler.select(valid, episode)
            feedback = self.normalizer.normalize_and_seal(self.gateway.review(pack_bundle(candidate, bundle)), len(episode.outcomes) + 1, defect.defect_id, bundle.diff)
            self.ledger.append(candidate, feedback)
            episode.add(candidate, feedback.outcome)
            self.scheduler.update(candidate, episode, feedback.outcome)
            if feedback.outcome is Outcome.MISSED:
                return Outcome.MISSED
            if feedback.outcome in {Outcome.UNREVIEWABLE, Outcome.ERROR} or not adaptive:
                return feedback.outcome
            families = [f for f in families if f.value not in episode.families]
        return Outcome.DETECTED
