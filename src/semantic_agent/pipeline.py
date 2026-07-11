from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .agent import GovernedAnalyticsAgent
from .contract import SemanticContract
from .data import prepare_data
from .evaluate import evaluate
from .integration import load_bundle, validate_snapshot_contracts
from .paths import ARTIFACTS

GENERATED_OUTPUTS = [
    "semantic_catalog_snapshot.json",
    "upstream_compatibility_report.json",
    "evaluation_results.json",
    "agent_traces.jsonl",
    "run_report.md",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_pipeline(artifact_dir: Path = ARTIFACTS, row_count: int = 480) -> dict[str, Any]:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    for path in artifact_dir.iterdir():
        if path.is_file():
            path.unlink()

    csv_path, database_path = prepare_data(rows=row_count)
    contract = SemanticContract()
    compatibility = validate_snapshot_contracts(contract)
    if not compatibility["passed"]:
        raise RuntimeError(f"Upstream compatibility failed: {compatibility['failures']}")

    write_json(artifact_dir / "semantic_catalog_snapshot.json", contract.catalog_snapshot())
    write_json(artifact_dir / "upstream_compatibility_report.json", compatibility)

    report = evaluate(
        GovernedAnalyticsAgent(database_path, contract=contract, measure_latency=False),
        artifact_dir / "evaluation_results.json",
        orders_csv_path=csv_path,
    )
    bundle = load_bundle(contract.upstream_bundle_path)
    upstream_refs = [
        {"repository": item["repository"], "commit_sha": item["commit_sha"]}
        for item in bundle["validated_repositories"]
    ]
    run_report = (
        "# Governed Semantic Agent Run Report\n\n"
        f"- Semantic contract: `{contract.version}`\n"
        f"- Upstream contract bundle: `{bundle['bundle_version']}`\n"
        f"- Upstream source contracts: {compatibility['source_count']}\n"
        f"- Metric bindings validated: {compatibility['metric_binding_count']}\n"
        f"- Dimension bindings validated: {compatibility['dimension_binding_count']}\n"
        f"- Evaluation cases: {report['case_count']}\n"
        f"- Answer correctness: {report['correctness_rate']:.0%}\n"
        f"- Independent grounding: {report['grounding_rate']:.0%}\n"
        f"- Lineage accuracy: {report['lineage_accuracy']:.0%}\n"
        f"- Refusal accuracy: {report['refusal_accuracy']:.0%}\n"
        f"- Release decision: **{report['release_decision'].upper()}**\n\n"
        "Recommendations remain pending human review. The agent executes no operational actions.\n"
    )
    (artifact_dir / "run_report.md").write_text(run_report, encoding="utf-8")

    output_hashes = {name: sha256(artifact_dir / name) for name in sorted(GENERATED_OUTPUTS)}
    manifest = {
        "manifest_version": "2.0.0",
        "contract_version": contract.version,
        "row_count": row_count,
        "inputs": {
            "orders_csv_sha256": sha256(csv_path),
            "semantic_contract_sha256": sha256(contract.path),
            "upstream_bundle_sha256": sha256(contract.upstream_bundle_path),
        },
        "upstream_repositories": upstream_refs,
        "outputs": output_hashes,
        "upstream_compatibility": "pass",
        "evaluation_release_decision": report["release_decision"],
    }
    write_json(artifact_dir / "artifact_manifest.json", manifest)
    return {
        "status": "complete",
        "contract_version": contract.version,
        "rows": row_count,
        "evaluation_cases": report["case_count"],
        "upstream_sources": compatibility["source_count"],
        "release_decision": report["release_decision"],
        "artifact_count": len(GENERATED_OUTPUTS) + 1,
    }


def main() -> None:
    print(json.dumps(run_pipeline(), sort_keys=True))


if __name__ == "__main__":
    main()
