"""A2: target-free planning from a frozen StrategyBank."""
from __future__ import annotations
from dataclasses import dataclass
from mira_mas.models import MessageFamily, VisibleFact


@dataclass(frozen=True)
class StrategyPlan:
    family: MessageFamily
    fact_ids: tuple[str, ...]


class NarrativeStrategist:
    def propose(self, facts: list[VisibleFact], family: MessageFamily) -> StrategyPlan:
        # No target feature or feedback is accepted by this method.
        visible = [fact for fact in facts if fact.kind in {"symbol", "changed-lines", "difficulty"}]
        return StrategyPlan(family=family, fact_ids=tuple(f.fact_id for f in visible[:4]))
