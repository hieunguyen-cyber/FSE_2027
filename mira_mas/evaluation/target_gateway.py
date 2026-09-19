"""Target boundary. It never forwards raw outputs to attacker agents."""
from __future__ import annotations
from typing import Protocol
from mira_mas.backends.cost import CostBudgetExceeded


class ReviewerAdapter(Protocol):
    def review(self, bundle: dict[str, str]) -> str: ...


class TargetGateway:
    def __init__(self, adapter: ReviewerAdapter, max_attempts: int = 2) -> None:
        if max_attempts <= 0:
            raise ValueError("max_attempts must be positive")
        self.adapter = adapter
        self.max_attempts = max_attempts

    def review(self, bundle: dict[str, str]) -> str:
        for _ in range(self.max_attempts):
            try:
                return self.adapter.review(bundle)
            except CostBudgetExceeded:
                raise
            except Exception:
                # Transport/provider details remain outside attacker feedback.
                continue
        return "ERROR"


class DeterministicSmokeAdapter:
    """Offline test double; no claim of victim reproduction."""
    def review(self, bundle: dict[str, str]) -> str:
        return "DETECTED: offline smoke adapter inspected the supplied diff."
