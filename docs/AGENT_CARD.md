# Agent Card

## Intended use

The agent answers four governed operational analytics questions defined in `config/semantic_contract.json`. It selects a canonical metric, generates SQL from a fixed semantic expression, validates read-only access, executes against SQLite, and records a trace.

## Capabilities and boundaries

- Reads only the `orders` analytical entity.
- Groups canonical metrics by an authorized dimension.
- Refuses questions that do not match the published contract.
- May propose investigation when a governed threshold is missed.
- Cannot modify data or execute an operational action.

## Evaluation

`evals/questions.json` contains balanced answer and refusal cases. `make verify` regenerates the evidence and requires 100% routing correctness and 100% refusal accuracy for this deliberately narrow contract.

## Known limitations

The classifier is deterministic and supports exact business questions, not free-form language. Data is synthetic and represents a local laboratory workflow. Estimated cost uses a documented token approximation; latency is measured on the local runtime. These results do not establish production performance.

