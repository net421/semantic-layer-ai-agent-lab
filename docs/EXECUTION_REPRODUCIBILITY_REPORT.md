# Execution Reproducibility Report

## Runtime contract

- Python: 3.11 or later.
- Runtime libraries: Python standard library only.
- Entry point: `make verify`.
- Random seed: `421`.
- Generated input rows: `360`.
- Database: local SQLite rebuilt on every verified run.

## Reproduction sequence

`make verify` removes the previous generated database and evidence bundle, regenerates the CSV, rebuilds the database, executes the closed evaluation set, runs the automated test suite and checks the release decision.

`artifacts/artifact_manifest.json` records SHA-256 hashes for the generated input and semantic contract. The input and governed query results are deterministic. Timestamps and measured latency are expected to vary by run and host; this nondeterminism is explicit and does not affect metric correctness or refusal results.

## Environment boundary

The workflow is validated on a local Python runtime and in GitHub Actions. It does not demonstrate workload scheduling, high concurrency, cloud data warehouse behavior or production service availability.
