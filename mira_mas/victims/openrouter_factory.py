"""Construct configured API reimplementations without exposing credentials to campaign state."""
from __future__ import annotations
import os
from mira_mas.backends.openrouter import OpenRouterChat, OpenRouterConfig
from mira_mas.victims.api_reproductions import ApiCodeAgentReviewer, ApiCodeReviewer
from mira_mas.backends.cost import CostMeter


def codeagent_from_env(max_qa_rounds: int = 1, meter: CostMeter | None = None) -> ApiCodeAgentReviewer:
    configured = os.environ.get("MIRA_CODEAGENT_QA_ROUNDS")
    if configured is not None:
        max_qa_rounds = int(configured)
    return ApiCodeAgentReviewer(OpenRouterChat(OpenRouterConfig.from_env(), meter), max_qa_rounds)


def codereviewer_from_env(meter: CostMeter | None = None) -> ApiCodeReviewer:
    return ApiCodeReviewer(OpenRouterChat(OpenRouterConfig.from_env(), meter))
