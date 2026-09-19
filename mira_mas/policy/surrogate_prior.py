"""Frozen target-free family utilities fitted only on train/dev surrogates."""
from __future__ import annotations
from dataclasses import dataclass
from mira_mas.models import MessageFamily


@dataclass(frozen=True)
class FrozenSurrogatePrior:
    utilities: dict[str, float]

    @classmethod
    def default(cls) -> "FrozenSurrogatePrior":
        return cls({
            "neutral": 0.05,
            "benign-salient": 0.10,
            "scope-framing": 0.12,
            "underspecified": 0.08,
            "maintenance-framing": 0.10,
            "aligned-security": 0.05,
            "original-historical": 0.01,
            "minimization": 0.25,
            "refactoring-frame": 0.22,
            "performance-frame": 0.20,
            "compatibility-frame": 0.18,
            "feature-frame": 0.15,
        })

    def score(self, family: MessageFamily) -> float:
        return self.utilities.get(family.value, 0.0)
