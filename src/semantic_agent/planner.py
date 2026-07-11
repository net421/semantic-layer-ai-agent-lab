import re

from .contract import QueryIntent, SemanticContract


INTENTS = {
    "show on-time delivery rate by region": QueryIntent("on_time_delivery_rate", "region"),
    "show fill rate by category": QueryIntent("fill_rate", "category"),
    "show net revenue by region": QueryIntent("net_revenue", "region"),
    "show average lead time by carrier": QueryIntent("average_lead_time_days", "carrier"),
}


def normalize_question(question: str) -> str:
    return re.sub(r"\s+", " ", question.strip().lower().rstrip("?.!"))


def classify(question: str) -> QueryIntent | None:
    return INTENTS.get(normalize_question(question))


def plan_sql(contract: SemanticContract, intent: QueryIntent) -> str:
    contract.validate_intent(intent)
    expression = contract.metric(intent.metric)["expression"]
    return (
        f'SELECT {intent.dimension} AS dimension_value, {expression} AS metric_value '
        f'FROM orders GROUP BY {intent.dimension} ORDER BY {intent.dimension} LIMIT 50'
    )

