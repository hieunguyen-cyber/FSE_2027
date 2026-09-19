"""A5: deterministic scheduling; outcomes change only cooldown/stopping, never the policy."""
from __future__ import annotations
from mira_mas.models import Candidate, EpisodeState, MessageFamily, Outcome
from mira_mas.policy.surrogate_prior import FrozenSurrogatePrior
import math


class DiversityScheduler:
    def __init__(self, prior: FrozenSurrogatePrior | None = None) -> None:
        self.prior = prior or FrozenSurrogatePrior.default()
        self.alpha: dict[str, float] = {}
        self.beta: dict[str, float] = {}

    @staticmethod
    def _difficulty(episode: EpisodeState) -> str:
        for fact in episode.facts:
            if fact.kind == "difficulty":
                return "high" if " high " in f" {fact.text} " else "medium" if " medium " in f" {fact.text} " else "low"
        return "unknown"

    def select(self, candidates: list[Candidate], episode: EpisodeState) -> Candidate:
        unused = [c for c in candidates if c.candidate_id not in episode.candidates]
        if not unused:
            raise ValueError("no untried, validated candidates")
        def score(candidate: Candidate) -> tuple[float, str]:
            key = f"{candidate.family.value}|{self._difficulty(episode)}"
            self.alpha.setdefault(key, 1.0)
            self.beta.setdefault(key, 1.0)
            mean = self.alpha[key] / (self.alpha[key] + self.beta[key])
            uncertainty = math.sqrt(2 * math.log(len(episode.outcomes) + 2) /
                                    (self.alpha[key] + self.beta[key]))
            value = self.prior.score(candidate.family) + 0.35 * mean + 0.15 * uncertainty
            if key not in episode.families:
                value += 0.05
            return value, candidate.candidate_id
        return max(unused, key=score)

    def update(self, candidate: Candidate, episode: EpisodeState, outcome: Outcome) -> None:
        """Update only from coarse outcome; raw target text never enters policy state."""
        key = f"{candidate.family.value}|{self._difficulty(episode)}"
        self.alpha.setdefault(key, 1.0)
        self.beta.setdefault(key, 1.0)
        if outcome is Outcome.MISSED:
            self.alpha[key] += 1.0
        elif outcome is Outcome.DETECTED:
            self.beta[key] += 1.0

    @staticmethod
    def next_action_allowed(outcome: Outcome) -> bool:
        return outcome is Outcome.DETECTED
