# Semantic Layer AI Agent Lab

A governed analytics agent that converts a versioned semantic catalog into
bounded read-only SQL, reconciles every permitted answer against an independent
reference implementation, records evidence lineage and validates its metric
contracts against the portfolio's dbt and cloud-warehouse repositories.

## What is integrated

This release pins and validates:

- `dbt-analytics-engineering-lab` model `fct_orders`;
- dbt mart `mart_supply_chain_kpis`;
- `cloud-warehouse-analytics-lab` relation
  `analytics.mart_order_fulfillment`.

GitHub Actions checks out both upstream repositories at exact commits and verifies
the reviewed SQL files by Git blob ID and required metric fragments. The agent
therefore fails closed when an upstream model drifts from the published semantic
contract.

## Architecture

```text
Pinned dbt + warehouse SQL contracts
              ↓
Versioned semantic catalog + aliases + source scopes
              ↓
Exact-question planner → read-only SQL guard → SQLite authorizer
              ↓
Grounded rows + independent Python reconciliation
              ↓
Lineage trace + optional human-review recommendation
              ↓
Evaluation, reproducibility and live-upstream CI gates
```

## Governed scope

The catalog publishes eight canonical metrics:

- unit fill rate;
- complete order rate;
- on-time delivery rate;
- OTIF rate;
- revenue;
- average order cycle time;
- total logistics cost;
- cost-to-serve percentage.

Shared upstream dimensions include warehouse, carrier and order date. Region is
classified as a warehouse enrichment. Category remains available only as a
clearly labeled local fixture for backward compatibility.

The planner authorizes 12 exact analytical questions and refuses all other
requests. It is intentionally not an unrestricted natural-language-to-SQL
system.

## Run locally

Requires CPython 3.12 and GNU Make. Runtime code uses the standard library.

```bash
make verify
```

This command:

1. validates the semantic/upstream snapshot bundle;
2. generates 480 deterministic fulfilled orders;
3. builds a read-only SQLite analytical fixture;
4. executes 20 answer/refusal evaluations;
5. reconciles every allowed result in independent Python;
6. runs the complete automated test suite;
7. verifies artifact hashes and release gates;
8. proves byte-identical evidence across two clean runs.

To validate actual local checkouts of the two upstream repositories:

```bash
make verify-live \
  DBT_ROOT=../dbt-analytics-engineering-lab \
  WAREHOUSE_ROOT=../cloud-warehouse-analytics-lab
```

## Evidence generated

- `semantic_catalog_snapshot.json`
- `upstream_compatibility_report.json`
- `evaluation_results.json`
- `agent_traces.jsonl`
- `run_report.md`
- `artifact_manifest.json`
- `live_upstream_validation.json` in the remote live gate

Generated data, databases and evidence are ignored by Git and uploaded by CI as
`semantic-agent-validation-evidence`.

## Safety and claim boundary

The SQL planner permits one generated `SELECT`, one approved table and at most 50
result rows. Text inspection and SQLite's authorizer both enforce the boundary.
Recommendations require human review and never execute actions.

This repository demonstrates a synthetic local agent and source-code-level
compatibility with pinned portfolio models. It does not claim a live production
warehouse connection, broad natural-language understanding, autonomous action,
enterprise identity controls or production monitoring.

See [`docs/UPSTREAM_INTEGRATION.md`](docs/UPSTREAM_INTEGRATION.md) and
[`docs/SEMANTIC_GOVERNANCE.md`](docs/SEMANTIC_GOVERNANCE.md).
