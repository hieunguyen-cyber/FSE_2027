"""Two-pass defense: code evidence first, metadata may request investigation but cannot erase evidence."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceReview:
    findings: tuple[str, ...]
    status: str


class BlindCodeFirstDefense:
    def reconcile(self, code_findings: list[str], commit_message: str) -> EvidenceReview:
        # Commit metadata is not treated as proof; absence of evidence is UNREVIEWABLE, never CLEAN.
        findings = tuple(code_findings)
        return EvidenceReview(findings=findings, status="DETECTED" if findings else "UNREVIEWABLE")
