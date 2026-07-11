from __future__ import annotations

from .contract import QueryIntent, SemanticContract


def normalize_question(question: str) -> str:
    return SemanticContract.normalize_question(question)


def classify(question: str, contract: SemanticContract | None = None) -> QueryIntent | None:
    return (contract or SemanticContract()).classify(question)


def plan_sql(contract: SemanticContract, intent: QueryIntent) -> str:
    contract.validate_intent(intent)
    expression = contract.metric(intent.metric)["expression"]
    dimension = intent.dimension
    return (
        f"SELECT {dimension} AS dimension_value, {expression} AS metric_value "
        f"FROM {contract.table} GROUP BY {dimension} ORDER BY {dimension} LIMIT 50"
    )
