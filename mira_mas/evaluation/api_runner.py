"""Run an explicitly configured OpenRouter reviewer through the normal gateway/firewall."""
from __future__ import annotations

import json
from pathlib import Path
from mira_mas.agents.orchestrator import CampaignOrchestrator
from mira_mas.agents.outcome_normalizer import OutcomeNormalizer
from mira_mas.evaluation.target_gateway import TargetGateway
from mira_mas.models import DefectCard, Outcome
from mira_mas.models import canonical_hash
from mira_mas.registry.immutable_ledger import ImmutableLedger
from mira_mas.backends.openrouter import OpenRouterConfig
from mira_mas.victims.openrouter_factory import codeagent_from_env, codereviewer_from_env
from mira_mas.evaluation.adjudication import blind_span_adjudication
from mira_mas.backends.cost import CostMeter


def run_openrouter_card(card: DefectCard, victim: str, output_dir: str | Path, budget: int = 1,
                        adaptive: bool = False, condition: str = "mira", cost_meter: CostMeter | None = None) -> Outcome:
    """Invoke one configured API reviewer; raw output remains in the isolated audit store."""
    reviewer = {"codeagent": codeagent_from_env, "codereviewer": codereviewer_from_env}.get(victim)
    if reviewer is None:
        raise ValueError("victim must be 'codeagent' or 'codereviewer'")
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    config = OpenRouterConfig.from_env()
    # Target-side metadata is reproducibility evidence; it excludes both the API key and raw response.
    metadata = {"victim": victim, "interface": "api-reimplementation", "condition": condition,
                "adaptive": adaptive, "budget": budget, "target_config": config.public_config(),
                "card_diff_hash": card.diff_hash, "card_context_hash": card.context_hash}
    metadata["metadata_hash"] = canonical_hash(metadata)
    (root / "target_metadata.json").write_text(json.dumps(metadata, sort_keys=True, indent=2), encoding="utf-8")
    target = reviewer(meter=cost_meter) if victim == "codeagent" else reviewer(cost_meter)
    return CampaignOrchestrator(
        TargetGateway(target), OutcomeNormalizer(root / "audit", blind_span_adjudication if victim == "codereviewer" else None), ImmutableLedger(root / "ledger.jsonl")
    ).run(card, budget=budget, adaptive=adaptive, condition=condition)
