"""Deterministic, bounded API evaluation over curated BigVul cards."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from mira_mas.data.splits import group_key
from mira_mas.evaluation.api_runner import run_openrouter_card
from mira_mas.models import DefectCard
from mira_mas.models import Outcome
from mira_mas.backends.cost import CostBudgetExceeded, CostMeter


def _group_hash(card: DefectCard) -> str:
    return sha256(repr(group_key(card)).encode()).hexdigest()


def select_cards(cards_jsonl: str | Path, split_manifest: str | Path, split: str, limit: int,
                 offset: int = 0) -> list[DefectCard]:
    """Choose a stable sample without exposing predicate labels to the target."""
    if limit <= 0:
        raise ValueError("limit must be positive")
    if offset < 0:
        raise ValueError("offset must be non-negative")
    manifest = json.loads(Path(split_manifest).read_text(encoding="utf-8"))
    memberships = {entry["group_hash"]: entry["split"] for entry in manifest["groups"]}
    selected: list[DefectCard] = []
    with Path(cards_jsonl).open(encoding="utf-8") as stream:
        for line in stream:
            card = DefectCard(**json.loads(line))
            if memberships.get(_group_hash(card)) == split:
                selected.append(card)
    selected.sort(key=lambda card: sha256(card.defect_id.encode()).hexdigest())
    return selected[offset:offset + limit]


def run_openrouter_sample(*, cards_jsonl: str | Path, split_manifest: str | Path, split: str,
                         limit: int, victim: str, output_dir: str | Path, offset: int = 0,
                         budget: int = 1, adaptive: bool = False, condition: str = "mira",
                         resume: bool = True, cost_budget_usd: float | None = None) -> dict[str, object]:
    """Run a bounded sample and write only per-card normalized outcomes to summary.json."""
    cards = select_cards(cards_jsonl, split_manifest, split, limit, offset=offset)
    if len(cards) < limit:
        raise ValueError(f"only {len(cards)} cards available for split={split!r}; requested {limit}")
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    records = []
    cost_state = root / "cost_meter.json"
    if resume and cost_state.exists():
        meter = CostMeter.from_dict(json.loads(cost_state.read_text(encoding="utf-8")), cost_budget_usd)
    else:
        meter = CostMeter(cost_budget_usd)
    stopped_reason = None
    for index, card in enumerate(cards, start=1):
        card_key = sha256(card.defect_id.encode()).hexdigest()[:12]
        card_root = root / f"card-{index:02d}-{card_key}"
        ledger_path = card_root / "ledger.jsonl"
        if resume and ledger_path.exists() and ledger_path.stat().st_size:
            last = json.loads(ledger_path.read_text(encoding="utf-8").splitlines()[-1])
            outcome = Outcome(last["feedback"]["outcome"])
        else:
            try:
                outcome = run_openrouter_card(card, victim, card_root, budget=budget,
                                              adaptive=adaptive, condition=condition, cost_meter=meter)
            except CostBudgetExceeded as error:
                stopped_reason = str(error)
                break
        records.append({"index": index, "defect_id": card.defect_id, "outcome": outcome.value})
        cost_state.write_text(json.dumps(meter.as_dict(), sort_keys=True, indent=2), encoding="utf-8")
    counts: dict[str, int] = {}
    for record in records:
        outcome = str(record["outcome"])
        counts[outcome] = counts.get(outcome, 0) + 1
    summary: dict[str, object] = {"victim": victim, "condition": condition, "adaptive": adaptive,
                                  "budget": budget, "split": split, "offset": offset, "requested": limit,
                                  "completed": len(records), "outcome_counts": counts, "records": records,
                                  "spent_usd": meter.spent_usd, "prompt_tokens": meter.prompt_tokens,
                                  "completion_tokens": meter.completion_tokens, "cost_budget_usd": cost_budget_usd,
                                  "stopped_reason": stopped_reason}
    (root / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2), encoding="utf-8")
    return summary
