from __future__ import annotations

import json
from pathlib import Path

from .paths import ARTIFACTS
from .pipeline import sha256


def verify_artifacts(artifact_dir: Path = ARTIFACTS) -> dict:
    artifact_dir = Path(artifact_dir)
    manifest_path = artifact_dir / "artifact_manifest.json"
    if not manifest_path.is_file():
        raise ValueError("Missing artifact_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    for name, expected_hash in manifest["outputs"].items():
        path = artifact_dir / name
        if not path.is_file() or path.stat().st_size == 0:
            failures.append(f"missing or empty output: {name}")
        elif sha256(path) != expected_hash:
            failures.append(f"hash mismatch: {name}")
    evaluation = json.loads((artifact_dir / "evaluation_results.json").read_text(encoding="utf-8"))
    compatibility = json.loads((artifact_dir / "upstream_compatibility_report.json").read_text(encoding="utf-8"))
    if evaluation["release_decision"] != "pass":
        failures.append("evaluation release gate failed")
    if not compatibility["passed"]:
        failures.append("upstream compatibility gate failed")
    return {"output_count": len(manifest["outputs"]), "passed": not failures, "failures": failures}


def main() -> None:
    report = verify_artifacts()
    if not report["passed"]:
        raise SystemExit(f"Artifact verification failed: {report['failures']}")
    print(f"Artifact verification passed: {report['output_count']} outputs")


if __name__ == "__main__":
    main()
