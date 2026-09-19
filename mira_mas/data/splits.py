"""Leakage-resistant, deterministic group splitting before policy development."""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
from mira_mas.models import DefectCard


def group_key(card: DefectCard) -> tuple[str, str, str]:
    return (card.project, card.cwe or "unknown", card.clone_cluster)


def grouped_split(cards: list[DefectCard], train_ratio: float = 0.70, dev_ratio: float = 0.15) -> dict[str, list[DefectCard]]:
    if not 0 < train_ratio < 1 or not 0 < dev_ratio < 1 or train_ratio + dev_ratio >= 1:
        raise ValueError("ratios must leave a non-empty test partition")
    groups: dict[tuple[str, str, str], list[DefectCard]] = defaultdict(list)
    for card in cards:
        groups[group_key(card)].append(card)
    splits = {"train": [], "dev": [], "test": []}
    for key, members in groups.items():
        bucket = int(sha256(repr(key).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
        name = "train" if bucket < train_ratio else "dev" if bucket < train_ratio + dev_ratio else "test"
        splits[name].extend(members)
    return splits


def write_split_manifest(cards_jsonl: str | Path, output_path: str | Path) -> dict[str, object]:
    """Create a compact preregistration manifest without copying DefectCard content."""
    groups: dict[tuple[str, str, str], int] = defaultdict(int)
    with Path(cards_jsonl).open(encoding="utf-8") as stream:
        for line in stream:
            item = json.loads(line)
            groups[(item["project"], item.get("cwe") or "unknown", item.get("clone_cluster") or "unknown")] += 1
    entries = []
    for key, count in sorted(groups.items()):
        bucket = int(sha256(repr(key).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
        split = "train" if bucket < 0.70 else "dev" if bucket < 0.85 else "test"
        entries.append({"group_hash": sha256(repr(key).encode()).hexdigest(), "split": split, "count": count})
    payload: dict[str, object] = {"version": "v1", "group_rule": "project*cwe*clone_cluster", "groups": entries}
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    return payload
