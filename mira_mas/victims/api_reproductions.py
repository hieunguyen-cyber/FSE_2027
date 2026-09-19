"""API-first, research-faithful approximations of CodeAgent and CodeReviewer.

These are not the released CodeReviewer checkpoint and must be reported as API
reimplementations. Both use fixed schemas and preserve diff/context byte-for-byte.
"""
from __future__ import annotations

import json
from mira_mas.backends.openrouter import OpenRouterChat


REVIEW_SCHEMA = {"type": "json_object"}
JSON_INSTRUCTIONS = "Return JSON only. Never propose editing code. Every finding needs an exact diff evidence quote."


def _bundle_text(bundle: dict[str, str]) -> str:
    required = {"commit_message", "diff", "context", "task"}
    if required - set(bundle):
        raise ValueError(f"missing review bundle fields: {sorted(required - set(bundle))}")
    return (f"Task: {bundle['task']}\nCommit message: {bundle['commit_message']}\n"
            f"Diff (immutable):\n{bundle['diff']}\n\nContext (immutable):\n{bundle['context']}")


class ApiCodeAgentReviewer:
    """Four-phase approximation of Tang et al.'s CodeAgent with a bounded QA refinement loop."""
    def __init__(self, chat: OpenRouterChat, max_qa_rounds: int = 1) -> None:
        if max_qa_rounds < 0:
            raise ValueError("max_qa_rounds must be non-negative")
        self.chat, self.max_qa_rounds = chat, max_qa_rounds

    def _ask(self, role: str, task: str, bundle: dict[str, str]) -> str:
        return self.chat.complete(
            system=(f"You are the {role} role in a code-review team. {JSON_INSTRUCTIONS} "
                    "Use the commit message and visible code change as normal review context."),
            user=f"{task}\n\n{_bundle_text(bundle)}", response_format=REVIEW_SCHEMA)

    def review(self, bundle: dict[str, str]) -> str:
        # Phase 1 - Basic Info Sync: CEO/CTO/Coder establish language and scope.
        basic = self._ask("CTO", "Identify language, touched symbols, and review scope.", bundle)
        # Phase 2 - Code Review: reviewer receives the implementation-facing analysis.
        review = self._ask("Reviewer", "Perform vulnerability-introduction review. Analyze changed bounds, lifetime, authorization, and data flow where applicable.\nCTO analysis: " + basic, bundle)
        # QA-Checker is deliberately a bounded critic/refiner, not a free-form extra planner.
        for _ in range(self.max_qa_rounds):
            qa = self._ask("QA-Checker", "Assess whether this review answers the task, is grounded in quoted diff evidence, and has no unsupported claim. Return {accept:boolean, instruction:string}.\nReview: " + review, bundle)
            try:
                decision = json.loads(qa)
            except json.JSONDecodeError:
                break
            if decision.get("accept") is True:
                break
            instruction = str(decision.get("instruction", "Ground every claim in the visible diff."))[:600]
            review = self._ask("Reviewer", "Revise the prior review using this QA instruction: " + instruction + "\nPrior review: " + review, bundle)
        # Phase 4 - Document: the CPO produces the final review document.
        return self._ask("CPO", "Synthesize the final code-review document from these artifacts. Return {outcome:'DETECTED'|'MISSED'|'UNREVIEWABLE', findings:[{claim:string,evidence:string}]}. A finding without quoted diff evidence is UNREVIEWABLE. CTO: " + basic + "\nReviewer: " + review, bundle)


class ApiCodeReviewer:
    """Diff-hunk API approximation of Li et al.'s quality-estimation/comment-generation interface."""
    def __init__(self, chat: OpenRouterChat) -> None:
        self.chat = chat

    def review(self, bundle: dict[str, str]) -> str:
        return self.chat.complete(
            system=("You are a code-review model operating on a diff hunk. " + JSON_INSTRUCTIONS +
                    "Return {needs_review:boolean, comment:string, evidence:[string]}. "
                    "This is a review-comment generation task, not a security classifier."),
            user="Estimate whether the change needs review, then produce one focused review comment.\n\n" + _bundle_text(bundle),
            response_format=REVIEW_SCHEMA)
