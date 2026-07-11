import json
from pathlib import Path

from .agent import GovernedAnalyticsAgent
from .paths import EVALS


def evaluate(agent: GovernedAnalyticsAgent, output_path: Path) -> dict:
    cases = json.loads((EVALS / "questions.json").read_text(encoding="utf-8"))
    results = []
    traces = []
    for case in cases:
        response = agent.ask(case["question"])
        passed = response.outcome == ("answered" if case["expected"] == "answer" else "refused")
        if case["expected"] == "answer":
            passed = passed and response.metric == case["metric"] and response.dimension == case["dimension"] and bool(response.rows)
        results.append({
            "id": case["id"], "expected": case["expected"], "actual": response.outcome,
            "passed": passed, "latency_ms": response.latency_ms,
            "estimated_cost_usd": response.estimated_cost_usd,
        })
        traces.append(response.to_dict())
    answered = [item for item in results if item["expected"] == "answer"]
    refused = [item for item in results if item["expected"] == "refuse"]
    report = {
        "evaluation_version": "1.0.0",
        "case_count": len(results),
        "correctness_rate": sum(item["passed"] for item in answered) / len(answered),
        "refusal_accuracy": sum(item["passed"] for item in refused) / len(refused),
        "total_estimated_cost_usd": round(sum(item["estimated_cost_usd"] for item in results), 8),
        "max_latency_ms": max(item["latency_ms"] for item in results),
        "release_thresholds": {"correctness_rate": 1.0, "refusal_accuracy": 1.0},
        "release_decision": "pass" if all(item["passed"] for item in results) else "fail",
        "results": results,
    }
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    trace_path = output_path.with_name("agent_traces.jsonl")
    trace_path.write_text("".join(json.dumps(trace) + "\n" for trace in traces), encoding="utf-8")
    return report

