import tempfile
import unittest
from pathlib import Path

from semantic_agent.agent import GovernedAnalyticsAgent
from semantic_agent.contract import SemanticContract
from semantic_agent.data import build_database, generate_orders, load_orders
from semantic_agent.reference import calculate_reference_rows, rows_match


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.csv_path = root / "orders.csv"
        self.database_path = root / "analytics.db"
        generate_orders(self.csv_path, rows=160)
        build_database(self.csv_path, self.database_path)
        self.contract = SemanticContract()
        self.agent = GovernedAnalyticsAgent(
            self.database_path, contract=self.contract, measure_latency=False
        )
        self.orders = load_orders(self.csv_path)

    def tearDown(self):
        self.directory.cleanup()

    def test_every_authorized_question_reconciles_independently(self):
        for question, intent in self.contract.questions.items():
            response = self.agent.ask(question)
            expected = calculate_reference_rows(
                self.orders, self.contract, intent.metric, intent.dimension
            )
            self.assertTrue(rows_match(response.rows, expected), question)

    def test_ratio_metrics_use_ratio_of_sums(self):
        response = self.agent.ask("Show unit fill rate by warehouse")
        self.assertIn("SUM(units_shipped)", response.sql)
        self.assertIn("SUM(units_ordered)", response.sql)

    def test_cost_to_serve_uses_additive_numerator_and_denominator(self):
        response = self.agent.ask("Show cost to serve percentage by warehouse")
        self.assertIn("SUM(total_logistics_cost)", response.sql)
        self.assertIn("SUM(order_revenue)", response.sql)


if __name__ == "__main__":
    unittest.main()
