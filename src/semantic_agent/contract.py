from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .paths import CONFIG, ROOT


@dataclass(frozen=True)
class QueryIntent:
    metric: str
    dimension: str
    source_scope: str | None = None


class SemanticContract:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or CONFIG / "semantic_contract.json"
        self.document = json.loads(self.path.read_text(encoding="utf-8"))
        self._validate_document()
        self._metric_aliases = self._build_metric_aliases()
        self._question_map = {
            self.normalize_question(item["question"]): QueryIntent(
                item["metric"], item["dimension"], item.get("source_scope")
            )
            for item in self.document["question_catalog"]
        }

    @staticmethod
    def normalize_question(question: str) -> str:
        return " ".join(question.strip().lower().rstrip("?.!").split())

    @property
    def version(self) -> str:
        return self.document["contract_version"]

    @property
    def table(self) -> str:
        return self.document["table"]

    @property
    def grain(self) -> str:
        return self.document["grain"]

    @property
    def upstream_bundle_path(self) -> Path:
        return ROOT / self.document["upstream_bundle"]

    @property
    def questions(self) -> dict[str, QueryIntent]:
        return dict(self._question_map)

    @property
    def allowed_dimensions(self) -> dict[str, dict[str, Any]]:
        return self.document["allowed_dimensions"]

    @property
    def metrics(self) -> dict[str, dict[str, Any]]:
        return self.document["metrics"]

    def classify(self, question: str) -> QueryIntent | None:
        return self._question_map.get(self.normalize_question(question))

    def canonical_metric_name(self, name: str) -> str:
        try:
            return self._metric_aliases[name]
        except KeyError as exc:
            raise ValueError(f"Metric is outside the semantic contract: {name}") from exc

    def metric(self, name: str) -> dict[str, Any]:
        return self.metrics[self.canonical_metric_name(name)]

    def dimension(self, name: str) -> dict[str, Any]:
        try:
            return self.allowed_dimensions[name]
        except KeyError as exc:
            raise ValueError(f"Dimension is outside the semantic contract: {name}") from exc

    def validate_intent(self, intent: QueryIntent) -> None:
        self.canonical_metric_name(intent.metric)
        self.dimension(intent.dimension)
        if intent.source_scope is not None:
            dimension_scope = self.dimension(intent.dimension)["scope"]
            if intent.source_scope != dimension_scope:
                raise ValueError(
                    f"Intent source scope {intent.source_scope!r} conflicts with dimension scope {dimension_scope!r}"
                )

    def lineage_for(self, intent: QueryIntent) -> dict[str, Any]:
        metric = self.metric(intent.metric)
        dimension = self.dimension(intent.dimension)
        shared = sorted(set(metric["upstream_support"]) & set(dimension["upstream_support"]))
        return {
            "entity": self.document["entity"],
            "local_relation": self.table,
            "grain": self.grain,
            "canonical_metric": self.canonical_metric_name(intent.metric),
            "requested_metric": intent.metric,
            "dimension": intent.dimension,
            "dimension_scope": dimension["scope"],
            "compatible_upstream_sources": shared,
        }

    def catalog_snapshot(self) -> dict[str, Any]:
        return self.document

    def _build_metric_aliases(self) -> dict[str, str]:
        aliases: dict[str, str] = {}
        for canonical, definition in self.metrics.items():
            aliases[canonical] = canonical
            for alias in definition.get("aliases", []):
                if alias in aliases:
                    raise ValueError(f"Duplicate metric alias: {alias}")
                aliases[alias] = canonical
        return aliases

    def _validate_document(self) -> None:
        required = {"contract_version", "entity", "table", "grain", "upstream_bundle", "allowed_dimensions", "metrics", "question_catalog", "refusal_topics"}
        missing = sorted(required - set(self.document))
        if missing:
            raise ValueError(f"Semantic contract is missing fields: {missing}")
        questions = [self.normalize_question(item["question"]) for item in self.document["question_catalog"]]
        if len(questions) != len(set(questions)):
            raise ValueError("Question catalog contains duplicate normalized questions")
