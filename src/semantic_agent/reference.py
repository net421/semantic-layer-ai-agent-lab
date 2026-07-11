from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any

from .contract import SemanticContract


def calculate_reference_rows(
    orders: list[dict[str, Any]],
    contract: SemanticContract,
    metric_name: str,
    dimension: str,
) -> list[dict[str, Any]]:
    canonical = contract.canonical_metric_name(metric_name)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in orders:
        grouped[str(row[dimension])].append(row)

    output: list[dict[str, Any]] = []
    for value in sorted(grouped):
        rows = grouped[value]
        if canonical == "unit_fill_rate":
            numerator = sum((Decimal(row["units_shipped"]) for row in rows), Decimal("0"))
            denominator = sum((Decimal(row["units_ordered"]) for row in rows), Decimal("0"))
            result = numerator / denominator if denominator else Decimal("0")
        elif canonical == "complete_order_rate":
            result = sum((Decimal(row["is_in_full"]) for row in rows), Decimal("0")) / Decimal(len(rows))
        elif canonical == "on_time_delivery_rate":
            result = sum((Decimal(row["is_on_time"]) for row in rows), Decimal("0")) / Decimal(len(rows))
        elif canonical == "otif_rate":
            result = sum((Decimal(row["is_otif"]) for row in rows), Decimal("0")) / Decimal(len(rows))
        elif canonical == "revenue":
            result = sum((row["order_revenue"] for row in rows), Decimal("0"))
        elif canonical == "average_order_cycle_time_days":
            result = sum((Decimal(row["order_cycle_time_days"]) for row in rows), Decimal("0")) / Decimal(len(rows))
        elif canonical == "total_logistics_cost":
            result = sum((row["total_logistics_cost"] for row in rows), Decimal("0"))
        elif canonical == "cost_to_serve_pct":
            numerator = sum((row["total_logistics_cost"] for row in rows), Decimal("0"))
            denominator = sum((row["order_revenue"] for row in rows), Decimal("0"))
            result = numerator / denominator if denominator else Decimal("0")
        else:
            raise ValueError(f"No reference implementation for metric: {canonical}")
        output.append({"dimension_value": value, "metric_value": float(result)})
    return output


def rows_match(
    actual: list[dict[str, Any]],
    expected: list[dict[str, Any]],
    tolerance: float = 1e-9,
) -> bool:
    if [row["dimension_value"] for row in actual] != [row["dimension_value"] for row in expected]:
        return False
    return all(
        abs(float(left["metric_value"]) - float(right["metric_value"])) <= tolerance
        for left, right in zip(actual, expected, strict=True)
    )
