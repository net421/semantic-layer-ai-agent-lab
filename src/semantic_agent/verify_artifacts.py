import json

from .paths import ARTIFACTS


def main() -> None:
    required = [
        "semantic_catalog_snapshot.json", "evaluation_results.json", "agent_traces.jsonl",
        "artifact_manifest.json", "run_report.md",
    ]
    missing = [name for name in required if not (ARTIFACTS / name).is_file() or (ARTIFACTS / name).stat().st_size == 0]
    if missing:
        raise SystemExit(f"Missing generated artifacts: {missing}")
    results = json.loads((ARTIFACTS / "evaluation_results.json").read_text(encoding="utf-8"))
    if results["release_decision"] != "pass":
        raise SystemExit("Evaluation gate failed")
    print("Artifact verification passed")


if __name__ == "__main__":
    main()

