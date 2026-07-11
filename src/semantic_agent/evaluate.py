from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .agent import GovernedAnalyticsAgent
from .contract import SemanticContract
from .data import load_orders
from .paths import EVALS
from .reference import calculate_reference_rows, rows_match


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def evaluate(
    agent: GovernedAnalyticsAgent,
    output_path: Path,
    orders_csv_path: Path | None = None,
) -> dict[str, Any]:
    cases = json.loads((EVALS / "questions.json").read_text(encoding="utf-8"))
    contract = agent.contract
    orders = load_orders(orders_csv_path) if orders_csv_path else None
    results: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []

    for case in cases:
        response = agent.ask(case["question"])
        expected_outcome = "answered" if case["expected"] == "answer" else "refused"
        passed = response.outcome == expected_outcome
        grounding_passed = True
        lineage_passed = True
        if case["expected"] == "answer":
            passed = (
                passed
                and response.metric == case["metric"]
                and response.dimension == case["dimension"]
                and bool(response.rows)
            )
            if orders is None:
                raise ValueError("orders_csv_path is required for answer reconciliation")
            expected_rows = calculate_reference_rows(
                orders, contract, case["metric"], case["dimension"]
            )
            grounding_passed = rows_match(response.rows, expected_rows)
            lineage_passed = (
                response.source_scope == case["source_scope"]
                and response.lineage is not None
                and response.lineage["dimension_scope"] == case["source_scope"]
            )
            if case["source_scope"] != "local_fixture_only":
                lineage_passed = lineage_passed and bool(
                    response.lineage["compatible_upstream_sources"]
                )
            passed = passed and grounding_passed and lineage_passed
        results.append(
            {
                "id": case["id"],
                "expected": case["expected"],
                "actual": response.outcome,
                "grounding_passed": grounding_passed,
                "lineage_passed": lineage_passed,
                "passed": passed,
                "estimated_cost_usd": response.estimated_cost_usd,
            }
        )
        traces.append(response.to_dict())

    answered = [item for item in results if item["expected"] == "answer"]
    refused = [item for item in results if item["expected"] == "refuse"]
    report = {
        "evaluation_version": "2.0.0",
        "case_count": len(results),
        "answer_case_count": len(answered),
        "refusal_case_count": len(refused),
        "correctness_rate": sum(item["passed"] for item in answered) / len(answered),
        "grounding_rate": sum(item["grounding_passed"] for item in answered) / len(answered),
        "lineage_accuracy": sum(item["lineage_passed"] for item in answered) / len(answered),
        "refusal_accuracy": sum(item["passed"] for item in refused) / len(refused),
        "total_estimated_cost_usd": round(
            sum(item["estimated_cost_usd"] for item in results), 8
        ),
        "release_thresholds": {
            "correctness_rate": 1.0,
            "grounding_rate": 1.0,
            "lineage_accuracy": 1.0,
            "refusal_accuracy": 1.0,
        },
        "release_decision": "pass" if all(item["passed"] for item in results) else "fail",
        "results": results,
    }
    _write_json(output_path, report)
    trace_path = output_path.with_name("agent_traces.jsonl")
    trace_path.write_text(
        "".join(json.dumps(trace, sort_keys=True) + "\n" for trace in traces),
        encoding="utf-8",
    )
    return report
