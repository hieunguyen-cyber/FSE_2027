"""Cost guard for bounded OpenRouter experiments."""
from __future__ import annotations
from dataclasses import dataclass

class CostBudgetExceeded(RuntimeError):
    pass

@dataclass
class CostMeter:
    budget_usd: float | None = None
    spent_usd: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @classmethod
    def from_dict(cls, value: dict[str, object], budget_usd: float | None = None) -> "CostMeter":
        return cls(budget_usd=budget_usd, spent_usd=float(value.get("spent_usd", 0.0)),
                   prompt_tokens=int(value.get("prompt_tokens", 0)),
                   completion_tokens=int(value.get("completion_tokens", 0)))

    def as_dict(self) -> dict[str, float | int]:
        return {"spent_usd": self.spent_usd, "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens}

    def record(self, prompt_tokens: int, completion_tokens: int, prompt_price: float, completion_price: float) -> None:
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.spent_usd += prompt_tokens * prompt_price + completion_tokens * completion_price
        if self.budget_usd is not None and self.spent_usd > self.budget_usd:
            raise CostBudgetExceeded(f"cost budget exceeded: ${self.spent_usd:.6f} > ${self.budget_usd:.2f}")
