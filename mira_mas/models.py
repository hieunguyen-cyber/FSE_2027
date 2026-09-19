"""Typed, hashable protocol objects. No object contains a raw target response."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
from typing import Any
import json


def canonical_hash(value: Any) -> str:
    """Stable SHA-256 for immutable protocol artifacts."""
    if not isinstance(value, str):
        value = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(value.encode("utf-8")).hexdigest()


class Outcome(str, Enum):
    DETECTED = "DETECTED"
    MISSED = "MISSED"
    UNREVIEWABLE = "UNREVIEWABLE"
    ERROR = "ERROR"


class MessageFamily(str, Enum):
    NEUTRAL = "neutral"
    BENIGN_SALIENT = "benign-salient"
    SCOPE_FRAMING = "scope-framing"
    UNDERSPECIFIED = "underspecified"
    MAINTENANCE_FRAMING = "maintenance-framing"
    ALIGNED_SECURITY = "aligned-security"
    ORIGINAL_HISTORICAL = "original-historical"
    MINIMIZATION = "minimization"
    REFACTORING_FRAME = "refactoring-frame"
    PERFORMANCE_FRAME = "performance-frame"
    COMPATIBILITY_FRAME = "compatibility-frame"
    FEATURE_FRAME = "feature-frame"


@dataclass(frozen=True)
class DefectCard:
    defect_id: str
    project: str
    commit: str
    cve: str | None
    cwe: str | None
    func_before: str
    func_after: str
    context: str = ""
    predicate: str | None = None  # curator-only: never given to attacker roles
    reviewable: bool = True
    clone_cluster: str = "unknown"
    historical_message: str = ""

    @property
    def reverse_diff(self) -> str:
        from difflib import unified_diff
        return "".join(unified_diff(
            self.func_after.splitlines(keepends=True), self.func_before.splitlines(keepends=True),
            fromfile="func_after", tofile="func_before", lineterm=""
        ))

    @property
    def diff_hash(self) -> str:
        return canonical_hash(self.reverse_diff)

    @property
    def context_hash(self) -> str:
        return canonical_hash(self.context)

    def public_bundle(self) -> dict[str, str]:
        return self.frozen_bundle().as_dict()

    def frozen_bundle(self) -> "ReviewBundle":
        return ReviewBundle(self.defect_id, self.reverse_diff, self.context, self.diff_hash, self.context_hash)


@dataclass(frozen=True)
class ReviewBundle:
    """The only DefectCard-derived object that may cross into attacker roles."""
    defect_id: str
    diff: str
    context: str
    diff_hash: str
    context_hash: str

    def as_dict(self) -> dict[str, str]:
        return {"defect_id": self.defect_id, "diff": self.diff, "context": self.context,
                "diff_hash": self.diff_hash, "context_hash": self.context_hash}


@dataclass(frozen=True)
class VisibleFact:
    fact_id: str
    kind: str
    text: str
    evidence: str
    certainty: str = "observed"


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    defect_id: str
    family: MessageFamily
    message: str
    visible_fact_ids: tuple[str, ...]
    template_version: str
    diff_hash: str
    context_hash: str
    validation: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, *, defect: DefectCard | ReviewBundle, family: MessageFamily, message: str,
               visible_fact_ids: list[str], template_version: str = "v1.0") -> "Candidate":
        bundle = defect.frozen_bundle() if isinstance(defect, DefectCard) else defect
        identity = canonical_hash({"defect_id": defect.defect_id, "family": family.value,
                                   "message": message, "template_version": template_version})
        return cls(identity, bundle.defect_id, family, message, tuple(visible_fact_ids), template_version,
                   bundle.diff_hash, bundle.context_hash)

    def with_validation(self, **items: Any) -> "Candidate":
        merged = dict(self.validation)
        merged.update(items)
        return Candidate(**{**asdict(self), "validation": merged})


@dataclass(frozen=True)
class NormalizedFeedback:
    round: int
    outcome: Outcome


@dataclass
class EpisodeState:
    """Serializable state intentionally limited to public facts and coarse outcomes."""
    defect_id: str
    facts: list[VisibleFact]
    budget: int
    candidates: list[str] = field(default_factory=list)
    families: list[str] = field(default_factory=list)
    outcomes: list[str] = field(default_factory=list)

    def add(self, candidate: Candidate, outcome: Outcome) -> None:
        self.candidates.append(candidate.candidate_id)
        self.families.append(candidate.family.value)
        self.outcomes.append(outcome.value)
        self.budget -= 1

    def to_public_json(self) -> str:
        return json.dumps({"defect_id": self.defect_id, "facts": [asdict(f) for f in self.facts],
                           "budget": self.budget, "candidates": self.candidates,
                           "families": self.families, "outcomes": self.outcomes}, sort_keys=True)
