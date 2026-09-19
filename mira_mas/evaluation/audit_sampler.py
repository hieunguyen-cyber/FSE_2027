"""Independent sampling of A4-accepted messages for factuality audit."""
from __future__ import annotations

import random
from mira_mas.models import Candidate


def sample_for_audit(candidates: list[Candidate], size: int, seed: int = 0) -> list[Candidate]:
    accepted = [c for c in candidates if c.validation.get("factuality") == "pass" and c.validation.get("policy") == "pass"]
    if size < 0:
        raise ValueError("size must be non-negative")
    return random.Random(seed).sample(accepted, min(size, len(accepted)))
