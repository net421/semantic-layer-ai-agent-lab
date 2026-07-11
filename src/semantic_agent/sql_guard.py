import re
import sqlite3


class UnsafeQuery(ValueError):
    """Raised when generated SQL violates the read-only policy."""


def validate_read_only_sql(sql: str, prohibited: list[str], allowed_table: str = "orders") -> None:
    normalized = re.sub(r"\s+", " ", sql.strip()).upper()
    if not normalized.startswith("SELECT "):
        raise UnsafeQuery("Only SELECT statements are permitted")
    if ";" in normalized:
        raise UnsafeQuery("Multiple statements are not permitted")
    for keyword in prohibited:
        if re.search(rf"\b{re.escape(keyword.upper())}\b", normalized):
            raise UnsafeQuery(f"Prohibited SQL keyword: {keyword}")
    tables = re.findall(r"\b(?:FROM|JOIN)\s+([A-Z_][A-Z0-9_]*)", normalized)
    if not tables or any(table.lower() != allowed_table for table in tables):
        raise UnsafeQuery("Query references an unauthorized table")
    limit_match = re.search(r"\bLIMIT\s+(\d+)", normalized)
    if not limit_match or int(limit_match.group(1)) > 50:
        raise UnsafeQuery("A result limit of 50 or fewer rows is required")


def install_sqlite_authorizer(connection: sqlite3.Connection, allowed_table: str = "orders") -> None:
    """Enforce table and function access in SQLite itself, beyond text inspection."""
    allowed_functions = {"avg", "julianday", "nullif", "sum"}

    def authorize(action, argument_one, argument_two, database_name, trigger_name):
        if action == sqlite3.SQLITE_SELECT:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_READ:
            return sqlite3.SQLITE_OK if argument_one == allowed_table else sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_FUNCTION:
            function_name = (argument_two or argument_one or "").lower()
            return sqlite3.SQLITE_OK if function_name in allowed_functions else sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_DENY

    connection.set_authorizer(authorize)
