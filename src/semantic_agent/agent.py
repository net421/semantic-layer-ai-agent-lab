from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .contract import SemanticContract
from .paths import CONFIG
from .planner import classify, plan_sql
from .sql_guard import install_sqlite_authorizer, validate_read_only_sql


@dataclass
class AgentResponse:
    question: str
    outcome: str
    reason: str
    contract_version: str
    metric: str | None
    dimension: str | None
    sql: str | None
    rows: list[dict[str, Any]]
    recommendation: dict[str, Any] | None
    trace: list[dict[str, Any]]
    estimated_tokens: int
    estimated_cost_usd: float
    latency_ms: float
    latency_measured: bool
    source_scope: str | None
    lineage: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GovernedAnalyticsAgent:
    def __init__(
        self,
        database_path: Path,
        contract: SemanticContract | None = None,
        measure_latency: bool = True,
    ) -> None:
        self.database_path = Path(database_path)
        self.contract = contract or SemanticContract()
        self.measure_latency = measure_latency
        self.policy = json.loads((CONFIG / "agent_policy.json").read_text(encoding="utf-8"))

    def ask(self, question: str) -> AgentResponse:
        started = time.perf_counter()
        trace: list[dict[str, Any]] = [{"stage": "classify", "status": "started"}]
        intent = classify(question, self.contract)
        if intent is None:
            trace[0]["status"] = "refused"
            return self._response(
                question,
                "refused",
                "Question is outside the authorized semantic contract",
                None,
                None,
                None,
                [],
                None,
                trace,
                started,
                None,
                None,
            )

        trace[0]["status"] = "passed"
        sql = plan_sql(self.contract, intent)
        lineage = self.contract.lineage_for(intent)
        trace.append(
            {
                "stage": "semantic_contract",
                "status": "passed",
                "metric": intent.metric,
                "canonical_metric": lineage["canonical_metric"],
                "dimension": intent.dimension,
                "source_scope": intent.source_scope,
                "compatible_upstream_sources": lineage["compatible_upstream_sources"],
            }
        )
        validate_read_only_sql(
            sql,
            self.policy["prohibited_sql"],
            allowed_table=self.contract.table,
            prohibited_tokens=self.policy["prohibited_sql_tokens"],
            maximum_rows=self.policy["maximum_result_rows"],
        )
        trace.append({"stage": "sql_policy", "status": "passed", "mode": "read_only"})

        connection = sqlite3.connect(f"file:{self.database_path}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        install_sqlite_authorizer(connection, self.contract.table)
        try:
            rows = [dict(row) for row in connection.execute(sql).fetchall()]
        finally:
            connection.close()
        trace.append({"stage": "execute", "status": "passed", "row_count": len(rows)})

        threshold = self.contract.metric(intent.metric)["minimum_acceptable"]
        below = [
            row
            for row in rows
            if threshold is not None and float(row["metric_value"]) < float(threshold)
        ]
        recommendation = None
        if below:
            recommendation = {
                "status": "human_review_required",
                "proposed_action": f"Investigate {intent.dimension} segments below the governed threshold",
                "affected_segments": [row["dimension_value"] for row in below],
                "agent_executed_action": False,
            }
        trace.append(
            {
                "stage": "recommendation",
                "status": "review_required" if recommendation else "not_required",
            }
        )
        return self._response(
            question,
            "answered",
            "Governed metric query executed successfully",
            intent.metric,
            intent.dimension,
            sql,
            rows,
            recommendation,
            trace,
            started,
            intent.source_scope,
            lineage,
        )

    def _response(
        self,
        question: str,
        outcome: str,
        reason: str,
        metric: str | None,
        dimension: str | None,
        sql: str | None,
        rows: list[dict[str, Any]],
        recommendation: dict[str, Any] | None,
        trace: list[dict[str, Any]],
        started: float,
        source_scope: str | None,
        lineage: dict[str, Any] | None,
    ) -> AgentResponse:
        output_chars = len(json.dumps(rows, sort_keys=True)) + len(reason)
        estimated_tokens = max(1, (len(question) + output_chars) // 4)
        model = self.policy["cost_model"]
        estimated_cost = (
            (len(question) // 4) * model["input_usd_per_million_tokens"]
            + (output_chars // 4) * model["output_usd_per_million_tokens"]
        ) / 1_000_000
        latency = round((time.perf_counter() - started) * 1000, 3) if self.measure_latency else 0.0
        return AgentResponse(
            question=question,
            outcome=outcome,
            reason=reason,
            contract_version=self.contract.version,
            metric=metric,
            dimension=dimension,
            sql=sql,
            rows=rows,
            recommendation=recommendation,
            trace=trace,
            estimated_tokens=estimated_tokens,
            estimated_cost_usd=round(estimated_cost, 8),
            latency_ms=latency,
            latency_measured=self.measure_latency,
            source_scope=source_scope,
            lineage=lineage,
        )
