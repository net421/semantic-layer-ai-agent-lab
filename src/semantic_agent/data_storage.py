from __future__ import annotations

import csv
import sqlite3
from decimal import Decimal
from pathlib import Path
from typing import Any

from .data_generation import COLUMNS, generate_orders
from .paths import DATA


def load_orders(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    integer_fields = {
        "units_ordered", "units_shipped", "is_in_full", "is_on_time",
        "is_otif", "order_cycle_time_days",
    }
    decimal_fields = {
        "unit_price", "order_revenue", "freight_cost", "handling_cost",
        "exception_cost", "total_logistics_cost", "cost_to_serve_pct",
    }
    typed: list[dict[str, Any]] = []
    for row in rows:
        converted: dict[str, Any] = dict(row)
        for field in integer_fields:
            converted[field] = int(row[field])
        for field in decimal_fields:
            converted[field] = Decimal(row[field])
        typed.append(converted)
    return typed


def build_database(csv_path: Path, database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        database_path.unlink()
    rows = load_orders(csv_path)
    connection = sqlite3.connect(database_path)
    try:
        connection.execute(
            """
            CREATE TABLE orders (
                order_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                order_date TEXT NOT NULL,
                promised_date TEXT NOT NULL,
                ship_date TEXT NOT NULL,
                delivered_date TEXT NOT NULL,
                region TEXT NOT NULL,
                category TEXT NOT NULL,
                warehouse TEXT NOT NULL,
                carrier TEXT NOT NULL,
                units_ordered INTEGER NOT NULL CHECK (units_ordered > 0),
                units_shipped INTEGER NOT NULL CHECK (units_shipped >= 0),
                unit_price REAL NOT NULL CHECK (unit_price > 0),
                order_revenue REAL NOT NULL CHECK (order_revenue >= 0),
                is_in_full INTEGER NOT NULL CHECK (is_in_full IN (0, 1)),
                is_on_time INTEGER NOT NULL CHECK (is_on_time IN (0, 1)),
                is_otif INTEGER NOT NULL CHECK (is_otif IN (0, 1)),
                order_cycle_time_days INTEGER NOT NULL CHECK (order_cycle_time_days >= 0),
                freight_cost REAL NOT NULL CHECK (freight_cost >= 0),
                handling_cost REAL NOT NULL CHECK (handling_cost >= 0),
                exception_cost REAL NOT NULL CHECK (exception_cost >= 0),
                total_logistics_cost REAL NOT NULL CHECK (total_logistics_cost >= 0),
                cost_to_serve_pct REAL NOT NULL CHECK (cost_to_serve_pct >= 0),
                CHECK (units_shipped <= units_ordered),
                CHECK (is_otif <= is_in_full),
                CHECK (is_otif <= is_on_time)
            )
            """
        )
        placeholders = ", ".join("?" for _ in COLUMNS)
        connection.executemany(
            f"INSERT INTO orders ({', '.join(COLUMNS)}) VALUES ({placeholders})",
            [
                tuple(
                    float(value) if isinstance(value, Decimal) else value
                    for value in (row[column] for column in COLUMNS)
                )
                for row in rows
            ],
        )
        connection.execute("CREATE VIEW fct_orders AS SELECT * FROM orders")
        connection.commit()
    finally:
        connection.close()


def prepare_data(rows: int = 480) -> tuple[Path, Path]:
    csv_path = DATA / "raw" / "orders.csv"
    database_path = DATA / "processed" / "analytics.db"
    generate_orders(csv_path, rows=rows)
    build_database(csv_path, database_path)
    return csv_path, database_path
