"""Hash all preregistered artifacts before a campaign."""
from __future__ import annotations
from pathlib import Path
from mira_mas.models import canonical_hash


def build_manifest(paths: list[str | Path]) -> dict[str, str]:
    return {str(Path(p)): canonical_hash(Path(p).read_bytes().hex()) for p in paths}


def verify_manifest(manifest: dict[str, str]) -> None:
    actual = build_manifest(list(manifest))
    if actual != manifest:
        raise ValueError("preregistered artifact hash mismatch")
