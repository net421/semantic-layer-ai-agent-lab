import csv
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from .paths import DATA


def generate_orders(path: Path, rows: int = 360, seed: int = 421) -> None:
    rng = random.Random(seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    regions = ["North", "South", "East", "West"]
    categories = ["Components", "Finished Goods", "Consumables"]
    carriers = ["Atlas", "BlueLine", "CargoOne"]
    start = date(2025, 1, 1)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "order_id", "order_date", "promised_date", "delivered_date", "region",
            "category", "carrier", "units_ordered", "units_shipped", "unit_price"
        ])
        for index in range(1, rows + 1):
            order_date = start + timedelta(days=rng.randrange(180))
            promised_days = rng.randint(3, 8)
            delay = rng.choices([-1, 0, 1, 2, 4], weights=[8, 55, 20, 12, 5])[0]
            promised_date = order_date + timedelta(days=promised_days)
            delivered_date = promised_date + timedelta(days=delay)
            units_ordered = rng.randint(5, 120)
            shortage = rng.choices([0, 1, 2, 5, 10], weights=[70, 12, 9, 6, 3])[0]
            units_shipped = max(0, units_ordered - shortage)
            writer.writerow([
                f"ORD-{index:04d}", order_date.isoformat(), promised_date.isoformat(),
                delivered_date.isoformat(), rng.choice(regions), rng.choice(categories),
                rng.choice(carriers), units_ordered, units_shipped, f"{rng.uniform(8, 180):.2f}"
            ])


def build_database(csv_path: Path, database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        database_path.unlink()
    connection = sqlite3.connect(database_path)
    try:
        connection.execute("""
            CREATE TABLE orders (
                order_id TEXT PRIMARY KEY,
                order_date TEXT NOT NULL,
                promised_date TEXT NOT NULL,
                delivered_date TEXT NOT NULL,
                region TEXT NOT NULL,
                category TEXT NOT NULL,
                carrier TEXT NOT NULL,
                units_ordered INTEGER NOT NULL CHECK (units_ordered > 0),
                units_shipped INTEGER NOT NULL CHECK (units_shipped >= 0),
                unit_price REAL NOT NULL CHECK (unit_price > 0),
                CHECK (units_shipped <= units_ordered)
            )
        """)
        with csv_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        connection.executemany(
            "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [tuple(row.values()) for row in rows],
        )
        connection.commit()
    finally:
        connection.close()


def prepare_data() -> tuple[Path, Path]:
    csv_path = DATA / "raw" / "orders.csv"
    database_path = DATA / "processed" / "analytics.db"
    generate_orders(csv_path)
    build_database(csv_path, database_path)
    return csv_path, database_path

