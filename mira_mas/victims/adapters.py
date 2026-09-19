"""Versioned adapters preserving victim-native inputs separately from common contract inputs."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class ReproductionRecord:
    name: str
    repository: str
    revision: str
    role: str
    interface: str
    status: str


def repository_revision(path: str | Path) -> str:
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


class CommonContractAdapter:
    """Base for adapter-dependent transfer runs; does not edit diff/context."""
    name = "abstract"
    def native_input(self, bundle: dict[str, str]) -> dict[str, str]:
        return dict(bundle)
    def review(self, bundle: dict[str, str]) -> str:
        raise RuntimeError("Configure the released victim checkpoint before evaluation")


class CodeAgentAdapter(CommonContractAdapter):
    name = "CodeAgent"
    def native_input(self, bundle: dict[str, str]) -> dict[str, str]:
        return {"ifcode": "commit", "commit": bundle["diff"], "commitmessage": bundle["commit_message"], "originalfile": bundle["context"]}


class CodeReviewerAdapter(CommonContractAdapter):
    name = "CodeReviewer"
    def native_input(self, bundle: dict[str, str]) -> dict[str, str]:
        return {"diff_hunk": bundle["diff"], "old_file": bundle["context"], "commit_message": bundle["commit_message"]}


class T5ReviewAdapter(CommonContractAdapter):
    name = "T5-code-review-automation"
    def native_input(self, bundle: dict[str, str]) -> dict[str, str]:
        return {"code_change": bundle["diff"], "context": bundle["context"], "commit_message": bundle["commit_message"]}
