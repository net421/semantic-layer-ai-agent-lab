from __future__ import annotations

import csv
import random
import sqlite3
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

from .paths import DATA

COLUMNS = [
    "order_id",
    "customer_id",
    "order_date",
    "promised_date",
    "ship_date",
    "delivered_date",
    "region",
    "category",
    "warehouse",
    "carrier",
    "units_ordered",
    "units_shipped",
    "unit_price",
    "order_revenue",
    "is_in_full",
    "is_on_time",
    "is_otif",
    "order_cycle_time_days",
    "freight_cost",
    "handling_cost",
    "exception_cost",
    "total_logistics_cost",
    "cost_to_serve_pct",
]


def _money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def generate_orders(path: Path, rows: int = 480, seed: int = 421) -> None:
    rng = random.Random(seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    regions = ["North", "South", "East", "West"]
    categories = ["Components", "Finished Goods", "Consumables"]
    warehouses = ["Dallas", "Chicago", "Reno"]
    carriers = ["Atlas", "BlueLine", "CargoOne"]
    start = date(2025, 1, 1)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        for index in range(1, rows + 1):
            order_date = start + timedelta(days=rng.randrange(240))
            promised_days = rng.randint(4, 9)
            cycle_days = max(1, promised_days + rng.choices([-1, 0, 1, 2, 4], [8, 55, 20, 12, 5])[0])
            promised_date = order_date + timedelta(days=promised_days)
            ship_date = order_date + timedelta(days=rng.randint(1, min(3, cycle_days)))
            delivered_date = order_date + timedelta(days=cycle_days)
            units_ordered = rng.randint(5, 120)
            shortage = rng.choices([0, 1, 2, 5, 10], [70, 12, 9, 6, 3])[0]
            units_shipped = max(0, units_ordered - shortage)
            unit_price = Decimal(str(round(rng.uniform(8, 180), 2)))
            order_revenue = Decimal(units_shipped) * unit_price
            is_in_full = int(units_shipped >= units_ordered)
            is_on_time = int(delivered_date <= promised_date)
            is_otif = int(is_in_full == 1 and is_on_time == 1)
            freight_cost = Decimal(str(round(rng.uniform(45, 320), 2)))
            handling_cost = Decimal(str(round(rng.uniform(8, 65), 2)))
            exception_cost = Decimal("0.00") if is_otif else Decimal(str(round(rng.uniform(5, 90), 2)))
            total_logistics_cost = freight_cost + handling_cost + exception_cost
            cost_to_serve = total_logistics_cost / order_revenue if order_revenue else Decimal("0")
            writer.writerow(
                {
                    "order_id": f"ORD-{index:05d}",
                    "customer_id": f"CUST-{rng.randint(1, 90):03d}",
                    "order_date": order_date.isoformat(),
                    "promised_date": promised_date.isoformat(),
                    "ship_date": ship_date.isoformat(),
                    "delivered_date": delivered_date.isoformat(),
                    "region": rng.choice(regions),
                    "category": rng.choice(categories),
                    "warehouse": rng.choice(warehouses),
                    "carrier": rng.choice(carriers),
                    "units_ordered": units_ordered,
                    "units_shipped": units_shipped,
                    "unit_price": _money(unit_price),
                    "order_revenue": _money(order_revenue),
                    "is_in_full": is_in_full,
                    "is_on_time": is_on_time,
                    "is_otif": is_otif,
                    "order_cycle_time_days": cycle_days,
                    "freight_cost": _money(freight_cost),
                    "handling_cost": _money(handling_cost),
                    "exception_cost": _money(exception_cost),
                    "total_logistics_cost": _money(total_logistics_cost),
                    "cost_to_serve_pct": str(cost_to_serve.quantize(Decimal("0.00000001"))),
                }
            )


def load_orders(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    integer_fields = {
        "units_ordered",
        "units_shipped",
        "is_in_full",
        "is_on_time",
        "is_otif",
        "order_cycle_time_days",
    }
    decimal_fields = {
        "unit_price",
        "order_revenue",
        "freight_cost",
        "handling_cost",
        "exception_cost",
        "total_logistics_cost",
        "cost_to_serve_pct",
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
                CHECK (is_otif <= is_in_ful),
                CHECK (is_otif <= is_on_time)
            )
            """
        )
        placeholders = ", ".join("?" for _ in COLUMNS)
        connection.executemany(
            f"INSERT INTO orders ({', '.join(COLUMNS)}) VALUES ({placeholders})",
            [tuple(float(value) if isinstance(value, Decimal) else value for value in (row[column] for column in COLUMNS)) for row in rows],
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
