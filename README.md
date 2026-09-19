# MIRA-MAS

Research implementation of a victim-isolated commit-message robustness assessment for C/C++ code review. It keeps the reverse diff and context hash-identical across all message conditions, gates message candidates with factuality/policy checks, and releases only normalized outcomes to the adaptive scheduler.

## Quick smoke test

```bash
python3 -m unittest discover -s mira_mas/tests -v
python3 -m mira_mas.cli --smoke
```

The `vendor/` directory is reserved for unmodified, pinned upstream victim/dataset snapshots. Real runs are deliberately not enabled until a released checkpoint and its native runtime are configured; the included smoke adapter is only an offline contract test.

## OpenRouter API reimplementations

`mira_mas.victims.ApiCodeAgentReviewer` is an API-first approximation of the four-phase CodeAgent pipeline (basic information sync, review, bounded QA-Checker refinement, document synthesis). `ApiCodeReviewer` recreates CodeReviewer's diff-hunk quality-estimation and review-comment-generation interface using an LLM API. They are **not** claims of reproducing the original local checkpoint; report them as API reimplementations/transfer reviewers.

Copy `.env.example` to a local, ignored `.env` or export `OPENROUTER_API_KEY` and `OPENROUTER_MODEL`. No API call is made by tests or the offline smoke runner.

To make a real, bounded API call after configuring those environment variables, write one curated DefectCard JSON object and run:

```bash
python3 -m mira_mas.cli --api-card path/to/card.json --victim codeagent --output artifacts/codeagent-run
```

The command sends only the frozen review bundle to the selected target; it seals raw output under `audit/` and prints only the normalized outcome.

## Full MIRA-MAS ASR protocol

Run each condition on the identical, group-disjoint test sample. `code-only` sends an empty commit-message field; `mira` generates policy-gated message candidates from the frozen diff, and `--adaptive` permits another distinct candidate only after `DETECTED`.

```bash
# Control
python3 -m mira_mas.cli --api-sample 10 --cards artifacts/curated/defect_cards.jsonl \
  --split-manifest artifacts/curated/split_manifest.json --victim codeagent \
  --condition code-only --output artifacts/asr-code-only

# MIRA-MAS, max three target calls per card
python3 -m mira_mas.cli --api-sample 10 --cards artifacts/curated/defect_cards.jsonl \
  --split-manifest artifacts/curated/split_manifest.json --victim codeagent \
  --condition mira --adaptive --budget 3 --output artifacts/asr-mira-adaptive
```

ASR is `MISSED / (MISSED + DETECTED)`. `ERROR` and `UNREVIEWABLE` are excluded. CodeReviewer comments require blind adjudication before they become resolved outcomes; they must not be scored directly as misses.

See [REPRODUCTION.md](REPRODUCTION.md) for the exact upstream snapshots and the distinction between the raw BigVul metadata CSV and its function-level cleaned release required by this protocol.
