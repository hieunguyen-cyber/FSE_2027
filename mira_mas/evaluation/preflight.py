"""Fail closed before a target campaign begins."""
from __future__ import annotations

import json
from pathlib import Path
from mira_mas.models import canonical_hash


REQUIRED_SPLITS = {"train", "dev", "test"}


def verify_campaign_inputs(cards_jsonl: str | Path, split_manifest: str | Path) -> dict[str, int]:
    cards = Path(cards_jsonl)
    manifest = Path(split_manifest)
    if not cards.is_file() or not cards.stat().st_size:
        raise ValueError("curated DefectCard JSONL is missing or empty")
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    groups = payload.get("groups", [])
    if not groups:
        raise ValueError("split manifest has no preregistered groups")
    names = {item.get("split") for item in groups}
    if not REQUIRED_SPLITS.issubset(names):
        raise ValueError("split manifest must contain train, dev, and test groups")
    return {"card_bytes": cards.stat().st_size, "group_count": len(groups), "manifest_hash": canonical_hash(payload)}
