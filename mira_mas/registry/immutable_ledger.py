"""Append-only hash-chained audit ledger; it contains normalized outcomes only."""
from __future__ import annotations
from dataclasses import asdict
import json
from pathlib import Path
from mira_mas.models import Candidate, NormalizedFeedback, canonical_hash


class ImmutableLedger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, candidate: Candidate, feedback: NormalizedFeedback) -> str:
        previous = "0" * 64
        if self.path.exists() and self.path.stat().st_size:
            previous = json.loads(self.path.read_text().splitlines()[-1])["entry_hash"]
        payload = {"candidate": asdict(candidate), "feedback": asdict(feedback), "previous_hash": previous}
        payload["feedback"]["outcome"] = feedback.outcome.value
        payload["entry_hash"] = canonical_hash(payload)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, sort_keys=True) + "\n")
        return payload["entry_hash"]
