import unittest
import sqlite3

from semantic_agent.sql_guard import UnsafeQuery, install_sqlite_authorizer, validate_read_only_sql


class SqlGuardTests(unittest.TestCase):
    def test_governed_select_is_allowed(self):
        validate_read_only_sql("SELECT region, COUNT(*) FROM orders GROUP BY region LIMIT 50", ["DELETE", "DROP"])

    def test_mutation_is_rejected(self):
        with self.assertRaises(UnsafeQuery):
            validate_read_only_sql("DELETE FROM orders", ["DELETE", "DROP"])

    def test_unknown_table_is_rejected(self):
        with self.assertRaises(UnsafeQuery):
            validate_read_only_sql("SELECT * FROM customers LIMIT 50", ["DELETE", "DROP"])

    def test_engine_denies_comma_join_to_sqlite_catalog(self):
        connection = sqlite3.connect(":memory:")
        connection.execute("CREATE TABLE orders (order_id TEXT)")
        install_sqlite_authorizer(connection)
        with self.assertRaises(sqlite3.DatabaseError):
            connection.execute(
                "SELECT orders.order_id, sqlite_master.name FROM orders, sqlite_master LIMIT 50"
            ).fetchall()
        connection.close()

    def test_engine_denies_table_valued_pragma(self):
        connection = sqlite3.connect(":memory:")
        connection.execute("CREATE TABLE orders (order_id TEXT)")
        install_sqlite_authorizer(connection)
        with self.assertRaises(sqlite3.DatabaseError):
            connection.execute(
                "SELECT orders.order_id FROM orders, pragma_table_info('orders') LIMIT 50"
            ).fetchall()
        connection.close()

    def test_engine_allows_governed_aggregate(self):
        connection = sqlite3.connect(":memory:")
        connection.execute("CREATE TABLE orders (region TEXT, units_ordered INTEGER, units_shipped INTEGER)")
        connection.execute("INSERT INTO orders VALUES ('North', 10, 9)")
        install_sqlite_authorizer(connection)
        rows = connection.execute(
            "SELECT region, SUM(units_shipped) * 1.0 / NULLIF(SUM(units_ordered), 0) "
            "FROM orders GROUP BY region LIMIT 50"
        ).fetchall()
        self.assertEqual([("North", 0.9)], rows)
        connection.close()


if __name__ == "__main__":
    unittest.main()
