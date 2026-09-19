"""Paired-condition reporting for MIRA-MAS experiments."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mira_mas.evaluation.scorer import asr_report, wilson_interval
from mira_mas.models import Outcome


def load_summary(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def paired_report(control_path: str | Path, treatment_path: str | Path) -> dict[str, Any]:
    control = load_summary(control_path)
    treatment = load_summary(treatment_path)
    control_map = {row["defect_id"]: Outcome(row["outcome"]) for row in control["records"]}
    treatment_map = {row["defect_id"]: Outcome(row["outcome"]) for row in treatment["records"]}
    ids = sorted(set(control_map) & set(treatment_map))
    pairs = [(control_map[key], treatment_map[key]) for key in ids]
    control_asr = asr_report([pair[0] for pair in pairs])
    treatment_asr = asr_report([pair[1] for pair in pairs])
    resolved = [(a, b) for a, b in pairs if a in {Outcome.DETECTED, Outcome.MISSED}
                and b in {Outcome.DETECTED, Outcome.MISSED}]
    treatment_misses = sum(b is Outcome.MISSED for _, b in resolved)
    low, high = wilson_interval(treatment_misses, len(resolved))
    return {"paired_cards": len(ids), "resolved_pairs": len(resolved),
            "control": control_asr, "treatment": treatment_asr,
            "treatment_wilson95": {"low": low, "high": high},
            "discordant": sum(a != b for a, b in resolved)}
