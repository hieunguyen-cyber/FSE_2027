from __future__ import annotations
import argparse
import json
from pathlib import Path
from mira_mas.agents.orchestrator import CampaignOrchestrator
from mira_mas.agents.outcome_normalizer import OutcomeNormalizer
from mira_mas.evaluation.target_gateway import DeterministicSmokeAdapter, TargetGateway
from mira_mas.models import DefectCard
from mira_mas.evaluation.api_runner import run_openrouter_card
from mira_mas.evaluation.batch_runner import run_openrouter_sample
from mira_mas.registry.immutable_ledger import ImmutableLedger
from mira_mas.data.curate import curate_clean_bigvul
from mira_mas.data.splits import write_split_manifest
from mira_mas.evaluation.preflight import verify_campaign_inputs
from mira_mas.evaluation.paired import paired_report


def main() -> None:
    parser = argparse.ArgumentParser(description="MIRA-MAS offline smoke runner")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--api-card", help="Path to one DefectCard JSON object for an OpenRouter-backed run.")
    parser.add_argument("--api-sample", type=int, help="Run a deterministic bounded BigVul sample through one API reviewer.")
    parser.add_argument("--victim", choices=("codeagent", "codereviewer"), help="API reimplementation to invoke.")
    parser.add_argument("--curate-bigvul", action="store_true", help="Create DefectCards from the cleaned BigVul CSV.")
    parser.add_argument("--input-csv", default="vendor/bigvul/MSR_data_cleaned.csv")
    parser.add_argument("--limit", type=int, help="Maximum cards for a bounded curation run.")
    parser.add_argument("--preflight", action="store_true", help="Validate curated cards and a non-empty split manifest.")
    parser.add_argument("--build-split", action="store_true", help="Write group-disjoint train/dev/test split manifest from curated cards.")
    parser.add_argument("--cards", help="Curated DefectCard JSONL for preflight.")
    parser.add_argument("--split-manifest", default="mira_mas/data/split_manifest.json")
    parser.add_argument("--sample-split", choices=("train", "dev", "test"), default="test")
    parser.add_argument("--sample-offset", type=int, default=0, help="Zero-based deterministic offset for --api-sample.")
    parser.add_argument("--condition", choices=("code-only", "historical", "mira"), default="mira")
    parser.add_argument("--adaptive", action="store_true", help="Enable outcome-bounded MIRA-MAS rounds.")
    parser.add_argument("--budget", type=int, default=1, help="Maximum target calls per card in adaptive MIRA-MAS.")
    parser.add_argument("--cost-budget-usd", type=float, help="Stop after measured OpenRouter cost exceeds this amount.")
    parser.add_argument("--paired-report", nargs=2, metavar=("CONTROL_SUMMARY", "TREATMENT_SUMMARY"))
    parser.add_argument("--output", default="artifacts/smoke")
    args = parser.parse_args()
    if args.paired_report:
        print(json.dumps(paired_report(*args.paired_report), sort_keys=True))
        return
    if args.curate_bigvul:
        print(curate_clean_bigvul(args.input_csv, args.output, args.limit))
        return
    if args.preflight:
        if not args.cards:
            parser.error("--preflight requires --cards")
        print(json.dumps(verify_campaign_inputs(args.cards, args.split_manifest), sort_keys=True))
        return
    if args.build_split:
        if not args.cards:
            parser.error("--build-split requires --cards")
        manifest = write_split_manifest(args.cards, args.split_manifest)
        print(len(manifest["groups"]))
        return
    if args.api_card:
        if not args.victim:
            parser.error("--api-card requires --victim")
        payload = json.loads(Path(args.api_card).read_text(encoding="utf-8"))
        print(run_openrouter_card(DefectCard(**payload), args.victim, args.output, budget=args.budget,
                                  adaptive=args.adaptive, condition=args.condition).value)
        return
    if args.api_sample:
        if not args.victim:
            parser.error("--api-sample requires --victim")
        if not args.cards:
            parser.error("--api-sample requires --cards")
        summary = run_openrouter_sample(cards_jsonl=args.cards, split_manifest=args.split_manifest,
                                        split=args.sample_split, limit=args.api_sample,
                                        victim=args.victim, output_dir=args.output, offset=args.sample_offset,
                                        budget=args.budget, adaptive=args.adaptive, condition=args.condition,
                                        cost_budget_usd=args.cost_budget_usd)
        print(json.dumps(summary["outcome_counts"], sort_keys=True))
        return
    if not args.smoke:
        parser.error("use --smoke or --api-card with --victim")
    output = Path(args.output)
    card = DefectCard("smoke-1", "demo", "demo", None, None, "int f(){ return 1; }\n", "int f(){ return 0; }\n")
    run = CampaignOrchestrator(TargetGateway(DeterministicSmokeAdapter()), OutcomeNormalizer(output / "audit"), ImmutableLedger(output / "ledger.jsonl"))
    print(run.run(card).value)


if __name__ == "__main__":
    main()
