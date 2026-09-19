# Reproduction map

For manual download instructions and checksums for files excluded from Git, see
[`DATASETS.md`](DATASETS.md).

The directories below are unmodified, shallow snapshots of the upstream implementations and data source. Their exact checked-out revision is recorded in [`mira_mas/victims/provenance.json`](mira_mas/victims/provenance.json).

| Protocol role | Local snapshot | Interface in this package |
| --- | --- | --- |
| Native primary security reviewer | `vendor/codeagent` | `CodeAgentAdapter` preserves its commit, commit-message, and context fields. |
| Transfer reviewer | `vendor/CodeBERT/CodeReviewer` | `CodeReviewerAdapter` exposes a common review bundle without editing code. |
| Transfer review-comment model | `vendor/code_review_automation` | `T5ReviewAdapter` exposes the common bundle; a blind security adjudicator is required to score a generated comment. |
| BigVul raw metadata | `vendor/bigvul/all_c_cpp_release2.0.csv` | Kept for provenance. It cannot form DefectCards because it lacks function pairs. |
| BigVul cleaned functions | `vendor/bigvul/MSR_data_cleaned.csv` | Needed by `mira_mas.data.curate`; download from the official upstream link and verify the two function columns. It is not present because its 1.54 GB download did not complete. |

## Intentional boundary

No real victim checkpoint is invoked by the offline smoke test. A production run must pin its released checkpoint, model/tokenizer hash, native/adapted interface, prompts, decoding parameters, parser version, and context-truncation rule before target evaluation. This prevents a passing local test from being mislabeled as a reproduced research result. The GitHub CodeAgent snapshot is present, but the authors' 30.7 MB full-source Zenodo archive could not be downloaded in this session; therefore no claim of a complete CodeAgent reproduction is made.

## API-first track

For the requested OpenRouter track, `ApiCodeAgentReviewer` follows the paper's role/phase pattern and retains a bounded QA-Checker loop. `ApiCodeReviewer` follows the paper's diff-hunk input and produces quality-estimation plus review-comment output. These are explicit API reimplementations, not a substitute for the released CodeReviewer checkpoint; they must be reported separately from native results.
