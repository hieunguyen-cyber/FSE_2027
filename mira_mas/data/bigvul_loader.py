"""BigVul ingestion, reviewability filtering, and reverse-patch construction."""
from __future__ import annotations

import csv
from pathlib import Path
import sys
from typing import Iterable
from mira_mas.models import DefectCard


ALIASES = {
    "func_before": ("func_before", "before", "vul_func"),
    "func_after": ("func_after", "after", "fix_func"),
    "project": ("project", "repo", "repo_name"),
    "commit": ("commit_id", "commit", "hash"),
    "cve": ("cve_id", "cve"),
    "cwe": ("cwe_id", "cwe"),
    "defect_id": ("id", "_id", "index"),
}


def _get(row: dict[str, str], name: str, default: str = "") -> str:
    for key in ALIASES[name]:
        if row.get(key):
            return row[key]
    return default


def is_c_cpp(row: dict[str, str]) -> bool:
    language = (row.get("language") or row.get("lang") or "").lower()
    return not language or language in {"c", "c++", "cpp", "c/c++"}


def is_reviewable(before: str, after: str, max_lines: int = 400) -> bool:
    return bool(before.strip() and after.strip() and before != after and
                max(len(before.splitlines()), len(after.splitlines())) <= max_lines)


def load_bigvul_csv(path: str | Path, max_lines: int = 400, vulnerable_only: bool = True) -> Iterable[DefectCard]:
    """Yield reviewable C/C++ cards from the function-level release.

    The cleaned release mixes non-vulnerable functions (``vul=0``) with the
    vulnerable function/fix pairs. The reverse-patch protocol operates only on
    the latter by default; this avoids treating an unchanged negative sample as
    a security-fix task.
    """
    # The official cleaned release contains occasional multi-megabyte patch fields.
    # Raise the stdlib parser ceiling before opening it; no field is retained unless a card is reviewable.
    try:
        csv.field_size_limit(sys.maxsize)
    except OverflowError:
        csv.field_size_limit(2**31 - 1)
    with Path(path).open(newline="", encoding="utf-8", errors="replace") as stream:
        reader = csv.DictReader(stream)
        fields = set(reader.fieldnames or [])
        if not {"func_before", "func_after"}.issubset(fields):
            raise ValueError(
                "This is the raw BigVul metadata snapshot, not the cleaned function-level release. "
                "Use MSR_data_cleaned.csv (or explicitly curate functions) before constructing DefectCards."
            )
        for ordinal, row in enumerate(reader):
            if not is_c_cpp(row):
                continue
            if vulnerable_only and str(row.get("vul", "")).strip().lower() not in {"1", "1.0", "true"}:
                continue
            before, after = _get(row, "func_before"), _get(row, "func_after")
            if not is_reviewable(before, after, max_lines):
                continue
            yield DefectCard(defect_id=_get(row, "defect_id", str(ordinal)), project=_get(row, "project", "unknown"),
                             commit=_get(row, "commit", "unknown"), cve=_get(row, "cve") or None,
                             cwe=_get(row, "cwe") or None, func_before=before, func_after=after,
                             context=row.get("context", ""), clone_cluster=row.get("clone_cluster", "unknown"),
                             historical_message=row.get("commit_message", ""))
