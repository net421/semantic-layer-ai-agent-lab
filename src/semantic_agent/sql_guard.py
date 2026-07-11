from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterable


class UnsafeQuery(ValueError):
    """Raised when generated SQL violates the read-only semantic policy."""


def _allowed_tables(value: str | Iterable[str]) -> set[str]:
    if isinstance(value, str):
        return {value.lower()}
    return {item.lower() for item in value}


def validate_read_only_sql(sql: str, prohibited: list[str], allowed_table: str | Iterable[str] = "orders", prohibited_tokens: list[str] | None = None, maximum_rows: int = 50) -> None:
    normalized = re.sub(r"\s+", " ", sql.strip())
    upper = normalized.upper()
    if not upper.startswith("SELECT "):
        raise UnsafeQuery("Only SELECT statements are permitted")
    if upper.count("SELECT ") != 1:
        raise UnsafeQuery("Nested or multiple SELECT statements are not permitted")
    if ";" in normalized:
        raise UnsafeQuery("Multiple statements are not permitted")
    for token in prohibited_tokens or []:
        if token.lower() in normalized.lower():
            raise UnsafeQuery(f"Prohibited SQL token: {token}")
    for keyword in prohibited:
        if re.search(rf"\b{re.escape(keyword.upper())}\b", upper):
            raise UnsafeQuery(f"Prohibited SQL keyword: {keyword}")
    tables = re.findall(r"\b(?:FROM|JOIN)\s+([A-Z_][A-Z0-9_]*)", upper)
    allowed = _allowed_tables(allowed_table)
    if not tables or any(table.lower() not in allowed for table in tables):
        raise UnsafeQuery("Query references an unauthorized table")
    limit_match = re.search(r"\bLIMIT\s+(\d+)", upper)
    if not limit_match or int(limit_match.group(1)) > maximum_rows:
        raise UnsafeQuery(f"A result limit of {maximum_rows} or fewer rows is required")


def install_sqlite_authorizer(connection: sqlite3.Connection, allowed_table: str | Iterable[str] = "orders") -> None:
    allowed_tables = _allowed_tables(allowed_table)
    allowed_functions = {"avg", "nullif", "sum"}
    def authorize(action, argument_one, argument_two, database_name, trigger_name):
        if action == sqlite3.SQLITE_SELECT:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_READ:
            return sqlite3.SQLITE_OK if (argument_one or "").lower() in allowed_tables else sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_FUNCTION:
            function_name = (argument_two or argument_one or "").lower()
            return sqlite3.SQLITE_OK if function_name in allowed_functions else sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_DENY
    connection.set_authorizer(authorize)
