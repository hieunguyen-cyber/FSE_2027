"""A6: sole component allowed to receive a raw response; only enum feedback leaves it."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Callable
from mira_mas.models import NormalizedFeedback, Outcome


class OutcomeNormalizer:
    def __init__(self, audit_store: str | Path,
                 adjudicator: Callable[[str, str], Outcome | None] | None = None) -> None:
        self.audit_store = Path(audit_store)
        self.audit_store.mkdir(parents=True, exist_ok=True)
        self.adjudicator = adjudicator

    def normalize_and_seal(self, raw: str, round_number: int, campaign_key: str,
                           frozen_diff: str = "") -> NormalizedFeedback:
        # Seal raw evidence independently; callers receive exactly two fields below.
        (self.audit_store / f"{campaign_key}-{round_number}.txt").write_text(raw, encoding="utf-8")
        try:
            declared = str(json.loads(raw).get("outcome", "")).upper()
        except (json.JSONDecodeError, AttributeError):
            declared = ""
        # Transfer-review comments may legitimately contain words such as
        # "error" or "missed".  Only an exact raw enum is a fallback verdict.
        raw_upper = raw.strip().upper()
        raw_label = raw_upper.split(":", 1)[0]
        upper = declared or raw_label
        adjudicated = self.adjudicator(raw, frozen_diff) if not declared and self.adjudicator else None
        if adjudicated is not None:
            return NormalizedFeedback(round=round_number, outcome=adjudicated)
        if upper == "UNREVIEWABLE":
            outcome = Outcome.UNREVIEWABLE
        elif upper == "ERROR":
            outcome = Outcome.ERROR
        elif upper == "MISSED":
            outcome = Outcome.MISSED
        elif upper == "DETECTED":
            outcome = Outcome.DETECTED
        else:
            # A transfer-reviewer response without a pre-registered security verdict is unresolved.
            outcome = Outcome.UNREVIEWABLE
        return NormalizedFeedback(round=round_number, outcome=outcome)
