"""A3: evidence-grounded semantic commit-message renderer.

The implementation deliberately stays deterministic for reproducible evaluation,
but uses structured claims and visible evidence rather than blindly formatting a
single static template.
"""
from __future__ import annotations
import json
from pathlib import Path
from mira_mas.agents.strategist import StrategyPlan
from mira_mas.models import Candidate, MessageFamily, ReviewBundle, VisibleFact


class MessageComposer:
    def __init__(self, registry_path: str | Path | None = None) -> None:
        registry_path = registry_path or Path(__file__).parents[1] / "policy" / "template_registry.yaml"
        self.registry = json.loads(Path(registry_path).read_text())

    def compose(self, bundle: ReviewBundle, plan: StrategyPlan, facts: list[VisibleFact]) -> Candidate:
        selected = [f for f in facts if f.fact_id in plan.fact_ids]
        symbols = [f.evidence for f in selected if f.kind == "symbol"]
        changes = [f.evidence for f in selected if f.kind == "changed-lines"]
        anchor = symbols[0] if symbols else "changed implementation"
        change = changes[0] if changes else "the visible patch"
        # Claims are intentionally modest and are checked again by A4.  This
        # avoids unsupported assertions such as "verified fix" or "no impact".
        messages: dict[MessageFamily, tuple[str, tuple[str, ...]]] = {
            MessageFamily.NEUTRAL: (f"Update the visible implementation around {anchor}.", ("implementation",)),
            MessageFamily.BENIGN_SALIENT: (f"Refine handling for {anchor} behavior in this patch.", ("implementation",)),
            MessageFamily.SCOPE_FRAMING: (f"Review the {anchor} path and its direct callers in this change.", ("scope",)),
            MessageFamily.UNDERSPECIFIED: (f"Update local implementation details around {change}.", ("implementation",)),
            MessageFamily.MAINTENANCE_FRAMING: (f"Simplify local handling around {anchor}.", ("maintenance",)),
            MessageFamily.ALIGNED_SECURITY: (f"Review the changed conditions around {anchor}.", ("review",)),
            MessageFamily.ORIGINAL_HISTORICAL: ("Preserve the original dataset summary for diagnostic comparison.", ("historical",)),
            MessageFamily.MINIMIZATION: (f"Refine the {anchor} error-handling edge case.", ("error-handling",)),
            MessageFamily.REFACTORING_FRAME: (f"Refactor {anchor} for clearer local control flow.", ("refactor",)),
            MessageFamily.PERFORMANCE_FRAME: (f"Tune the {anchor} path while preserving the visible behavior.", ("performance",)),
            MessageFamily.COMPATIBILITY_FRAME: (f"Adjust {anchor} handling for the surrounding interface.", ("compatibility",)),
            MessageFamily.FEATURE_FRAME: (f"Extend {anchor} handling with the visible validation change.", ("validation",)),
        }
        message, claims = messages[plan.family]
        candidate = Candidate.create(defect=bundle, family=plan.family, message=message,
                                     visible_fact_ids=list(plan.fact_ids), template_version="semantic-v3")
        return candidate.with_validation(claims=list(claims), anchor=anchor, evidence=changes[:1] or ["diff"])
