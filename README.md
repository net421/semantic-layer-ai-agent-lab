# Semantic Layer AI Agent Lab

A complete local laboratory for governed analytical questions. It turns a versioned semantic contract into validated read-only SQL, executes against a reproducible supply-chain dataset, records evidence traces, evaluates correct refusals, and routes recommendations to human review.

## Evidence summary

| Capability | Inspectable evidence | Validation |
|---|---|---|
| Governed metrics | `config/semantic_contract.json` | Contract tests and catalog snapshot |
| Agent scope | `src/semantic_agent/planner.py` | Four allowed and four refused eval cases |
| Safe SQL | `src/semantic_agent/sql_guard.py` | Mutation/table policy tests |
| Grounded answers | `artifacts/agent_traces.jsonl` | SQL, rows, contract version and stages retained |
| Human control | `docs/TOOL_ACCESS_AND_APPROVAL_CONTRACT.md` | Recommendations cannot execute actions |
| Quality gate | `artifacts/evaluation_results.json` | Correctness and refusal thresholds |

## Business problem

Analysts and AI systems can produce conflicting answers when KPI definitions, grouping dimensions and source tables are implicit. This lab publishes one narrow operational semantic contract and forces every supported answer through that contract.

## Architecture

```text
Deterministic orders -> SQLite analytical entity -> semantic intent
  -> governed SQL planner -> read-only SQL guard -> result rows
  -> trace + optional recommendation -> human review
```

## Run from a clean checkout

Requirements: Python 3.11+ and GNU Make. Runtime code uses only the Python standard library.

```bash
make verify
```

The command deletes prior generated outputs, creates 360 deterministic orders, builds the SQLite database, executes eight evaluation cases, writes the evidence bundle, runs eleven automated tests, and verifies the release decision.

## Generated evidence

| Artifact | Purpose |
|---|---|
| `artifacts/semantic_catalog_snapshot.json` | Exact contract used by the run |
| `artifacts/evaluation_results.json` | Per-case results, thresholds and release decision |
| `artifacts/agent_traces.jsonl` | Full answer/refusal traces with SQL, rows, cost and latency |
| `artifacts/artifact_manifest.json` | Input hashes and generated output inventory |
| `artifacts/run_report.md` | Human-readable run summary |

## Supported questions

- Show on-time delivery rate by region.
- Show fill rate by category.
- Show net revenue by region.
- Show average lead time by carrier.

Other questions are refused. This is intentional evidence of scope control.

## Claim boundary

This repository demonstrates a synthetic, local, governed analytics pattern. It does not claim an enterprise semantic platform, unrestricted natural-language understanding, autonomous decisions, live cloud deployment or production monitoring. The evaluation result applies only to the published cases and versioned contract.

## Repository structure

```text
config/       semantic and tool policies
data/         reproducible input and local database
evals/        answer/refusal evaluation dataset
src/          data, contract, planner, guard, agent and pipeline
tests/        contract, policy and agent tests
artifacts/    generated evidence bundle
docs/         agent card, evaluation and approval contracts
```
