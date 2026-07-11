import json
from dataclasses import dataclass
from pathlib import Path

from .paths import CONFIG


@dataclass(frozen=True)
class QueryIntent:
    metric: str
    dimension: str


class SemanticContract:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or CONFIG / "semantic_contract.json"
        self.document = json.loads(self.path.read_text(encoding="utf-8"))

    @property
    def version(self) -> str:
        return self.document["contract_version"]

    def validate_intent(self, intent: QueryIntent) -> None:
        if intent.metric not in self.document["metrics"]:
            raise ValueError(f"Metric is outside the semantic contract: {intent.metric}")
        if intent.dimension not in self.document["allowed_dimensions"]:
            raise ValueError(f"Dimension is outside the semantic contract: {intent.dimension}")

    def metric(self, name: str) -> dict:
        return self.document["metrics"][name]

