import hashlib
import json
from datetime import datetime, timezone

from .agent import GovernedAnalyticsAgent
from .data import prepare_data
from .evaluate import evaluate
from .paths import ARTIFACTS, CONFIG


def sha256(path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    csv_path, database_path = prepare_data()
    contract_path = CONFIG / "semantic_contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    (ARTIFACTS / "semantic_catalog_snapshot.json").write_text(
        json.dumps(contract, indent=2) + "\n", encoding="utf-8"
    )
    report = evaluate(GovernedAnalyticsAgent(database_path), ARTIFACTS / "evaluation_results.json")
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "contract_version": contract["contract_version"],
        "inputs": {"orders_csv_sha256": sha256(csv_path), "semantic_contract_sha256": sha256(contract_path)},
        "outputs": ["semantic_catalog_snapshot.json", "evaluation_results.json", "agent_traces.jsonl", "run_report.md"],
        "evaluation_release_decision": report["release_decision"],
    }
    (ARTIFACTS / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (ARTIFACTS / "run_report.md").write_text(
        "# Governed Agent Run Report\n\n"
        f"- Contract version: `{contract['contract_version']}`\n"
        f"- Evaluation cases: {report['case_count']}\n"
        f"- Metric correctness: {report['correctness_rate']:.0%}\n"
        f"- Refusal accuracy: {report['refusal_accuracy']:.0%}\n"
        f"- Release decision: **{report['release_decision'].upper()}**\n"
        f"- Maximum observed local latency: {report['max_latency_ms']:.3f} ms\n"
        f"- Estimated evaluation cost: ${report['total_estimated_cost_usd']:.8f}\n\n"
        "Recommendations, when present, remain pending human review; the agent cannot execute operational actions.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "complete", "release_decision": report["release_decision"], "artifacts": len(manifest["outputs"])}))


if __name__ == "__main__":
    main()

