"""A4: factuality, policy, hash, and duplicate gate before target submission."""
from __future__ import annotations
from dataclasses import dataclass
import re
from mira_mas.models import Candidate, ReviewBundle, VisibleFact


FORBIDDEN = re.compile(r"\b(ignore|disregard|system prompt|developer message|roleplay|jailbreak|no security impact|verified fix|no functional change|trivial|all input variants|always safe|secure)\b", re.I)


@dataclass(frozen=True)
class CriticVerdict:
    accepted: bool
    tags: tuple[str, ...]


class FactualityPolicyCritic:
    def validate(self, candidate: Candidate, bundle: ReviewBundle, facts: list[VisibleFact], seen_messages: set[str]) -> CriticVerdict:
        tags = []
        if candidate.diff_hash != bundle.diff_hash or candidate.context_hash != bundle.context_hash:
            tags.append("hash-mismatch")
        if candidate.message in seen_messages:
            tags.append("duplicate")
        if FORBIDDEN.search(candidate.message):
            tags.append("forbidden-content")
        if len(candidate.message.split()) < 2 or len(candidate.message) > 240:
            tags.append("unreviewable-message")
        fact_ids = {f.fact_id for f in facts}
        if not set(candidate.visible_fact_ids).issubset(fact_ids):
            tags.append("unknown-fact")
        selected = [f for f in facts if f.fact_id in candidate.visible_fact_ids]
        if not selected:
            tags.append("no-visible-evidence")
        claims = set(candidate.validation.get("claims", []))
        evidence_text = " ".join(f"{f.text} {f.evidence}" for f in selected).lower()
        claim_markers = {
            "performance": ("performance", "latency", "overhead", "loop", "path"),
            "compatibility": ("compat", "interface", "platform", "api"),
            "validation": ("valid", "check", "condition", "guard", "assert"),
            "error-handling": ("error", "fail", "return", "exception", "null"),
            "scope": ("caller", "function", "path"),
        }
        for claim in claims:
            markers = claim_markers.get(claim)
            if markers and not any(marker in evidence_text for marker in markers):
                tags.append(f"unsupported-claim:{claim}")
        return CriticVerdict(not tags, tuple(tags))
