from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .contract import SemanticContract


class IntegrationContractError(ValueError):
    """Raised when a semantic/upstream contract is incompatible or stale."""


def git_blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("utf-8")
    return hashlib.sha1(header + content).hexdigest()


def load_bundle(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if "sources" not in document or not document["sources"]:
        raise IntegrationContractError("Upstream contract bundle has no sources")
    return document


def _validate_sha(value: str, name: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise IntegrationContractError(f"{name} must be a 40-character lowercase SHA")


def validate_snapshot_contracts(contract: SemanticContract) -> dict[str, Any]:
    bundle = load_bundle(contract.upstream_bundle_path)
    source_results: list[dict[str, Any]] = []
    failures: list[str] = []

    for source_id, source in sorted(bundle["sources"].items()):
        source_failures: list[str] = []
        try:
            _validate_sha(source["commit_sha"], f"{source_id}.commit_sha")
            _validate_sha(source["git_blob_sha"], f"{source_id}.git_blob_sha")
        except IntegrationContractError as exc:
            source_failures.append(str(exc))
        if not source.get("columns"):
            source_failures.append("columns are empty")
        if not source.get("metric_formula_ids"):
            source_failures.append("metric formula mapping is empty")
        source_results.append(
            {
                "source_id": source_id,
                "repository": source["repository"],
                "commit_sha": source["commit_sha"],
                "relation": source["relation"],
                "grain": source["grain"],
                "passed": not source_failures,
                "failures": source_failures,
            }
        )
        failures.extend(f"{source_id}: {failure}" for failure in source_failures)

    metric_results: list[dict[str, Any]] = []
    for metric_name, metric in sorted(contract.metrics.items()):
        for source_id in metric["upstream_support"]:
            source = bundle["sources"].get(source_id)
            expected = metric["formula_id"]
            actual = None if source is None else source["metric_formula_ids"].get(metric_name)
            passed = actual == expected
            metric_results.append(
                {
                    "metric": metric_name,
                    "source_id": source_id,
                    "expected_formula_id": expected,
                    "actual_formula_id": actual,
                    "passed": passed,
                }
            )
            if not passed:
                failures.append(
                    f"{metric_name}/{source_id}: expected {expected!r}, found {actual!r}"
                )

    dimension_results: list[dict[str, Any]] = []
    for dimension_name, dimension in sorted(contract.allowed_dimensions.items()):
        for source_id in dimension["upstream_support"]:
            source = bundle["sources"].get(source_id)
            columns = set() if source is None else set(source["columns"])
            passed = dimension_name in columns
            dimension_results.append(
                {
                    "dimension": dimension_name,
                    "source_id": source_id,
                    "passed": passed,
                }
            )
            if not passed:
                failures.append(f"{dimension_name}/{source_id}: dimension column not found")

    return {
        "bundle_version": bundle["bundle_version"],
        "semantic_contract_version": contract.version,
        "source_count": len(source_results),
        "metric_binding_count": len(metric_results),
        "dimension_binding_count": len(dimension_results),
        "sources": source_results,
        "metric_bindings": metric_results,
        "dimension_bindings": dimension_results,
        "passed": not failures,
        "failures": failures,
    }


def validate_live_upstreams(
    contract: SemanticContract,
    dbt_root: Path,
    warehouse_root: Path,
) -> dict[str, Any]:
    bundle = load_bundle(contract.upstream_bundle_path)
    roots = {
        "net421/dbt-analytics-engineering-lab": Path(dbt_root),
        "net421/cloud-warehouse-analytics-lab": Path(warehouse_root),
    }
    results: list[dict[str, Any]] = []
    failures: list[str] = []
    for source_id, source in sorted(bundle["sources"].items()):
        root = roots.get(source["repository"])
        source_failures: list[str] = []
        if root is None:
            source_failures.append("no checkout root supplied")
            path = Path(source["source_file"])
        else:
            path = root / source["source_file"]
            if not path.is_file():
                source_failures.append(f"missing source file: {path}")
            else:
                content = path.read_bytes()
                actual_blob_sha = git_blob_sha(content)
                if actual_blob_sha != source["git_blob_sha"]:
                    source_failures.append(
                        f"git blob drift: expected {source['git_blob_sha']}, found {actual_blob_sha}"
                    )
                text = content.decode("utf-8").lower()
                for fragment in source["required_fragments"]:
                    if fragment.lower() not in text:
                        source_failures.append(f"required SQL fragment missing: {fragment}")
        results.append(
            {
                "source_id": source_id,
                "path": str(path),
                "expected_commit_sha": source["commit_sha"],
                "expected_git_blob_sha": source["git_blob_sha"],
                "passed": not source_failures,
                "failures": source_failures,
            }
        )
        failures.extend(f"{source_id}: {failure}" for failure in source_failures)
    return {
        "source_count": len(results),
        "sources": results,
        "passed": not failures,
        "failures": failures,
    }
