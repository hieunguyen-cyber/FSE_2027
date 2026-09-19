"""Build immutable, hash-checked target input bundles."""
from __future__ import annotations
from dataclasses import asdict
from mira_mas.models import Candidate, DefectCard, ReviewBundle, canonical_hash


def pack_bundle(candidate: Candidate, defect: DefectCard | ReviewBundle) -> dict[str, str]:
    frozen = defect.frozen_bundle() if isinstance(defect, DefectCard) else defect
    if (candidate.diff_hash, candidate.context_hash) != (frozen.diff_hash, frozen.context_hash):
        raise ValueError("candidate does not match frozen DefectCard")
    bundle = {"commit_message": candidate.message, "diff": frozen.diff, "context": frozen.context, "task": "review"}
    bundle["bundle_hash"] = canonical_hash(bundle)
    return bundle
