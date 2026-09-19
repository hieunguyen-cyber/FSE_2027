"""Explicit DefectCard curation with no target reviewer dependency."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from mira_mas.data.bigvul_loader import load_bigvul_csv


def curate_clean_bigvul(input_csv: str | Path, output_jsonl: str | Path, limit: int | None = None) -> int:
    """Emit only reviewable C/C++ function cards from the official cleaned BigVul release.

    The raw upstream CSV is intentionally rejected because it lacks the function pairs
    required by the document's reverse-patch protocol.
    """
    output = Path(output_jsonl)
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", encoding="utf-8") as stream:
        for card in load_bigvul_csv(input_csv):
            stream.write(json.dumps(asdict(card), ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
            if limit is not None and count >= limit:
                break
    return count
