import tempfile
import unittest
from pathlib import Path

from semantic_agent.agent import GovernedAnalyticsAgent
from semantic_agent.data import build_database, generate_orders


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        csv_path = root / "orders.csv"
        self.database_path = root / "analytics.db"
        generate_orders(csv_path, rows=80)
        build_database(csv_path, self.database_path)
        self.agent = GovernedAnalyticsAgent(self.database_path, measure_latency=False)

    def tearDown(self):
        self.directory.cleanup()

    def test_authorized_question_returns_grounded_rows(self):
        response = self.agent.ask("Show fill rate by category")
        self.assertEqual("answered", response.outcome)
        self.assertEqual("fill_rate", response.metric)
        self.assertGreater(len(response.rows), 0)
        self.assertIn("FROM orders", response.sql)

    def test_out_of_scope_question_is_refused(self):
        response = self.agent.ask("List customer names and addresses")
        self.assertEqual("refused", response.outcome)
        self.assertEqual([], response.rows)

    def test_agent_never_executes_recommended_action(self):
        response = self.agent.ask("Show on-time delivery rate by region")
        if response.recommendation:
            self.assertFalse(response.recommendation["agent_executed_action"])

    def test_shared_question_returns_upstream_lineage(self):
        response = self.agent.ask("Show unit fill rate by warehouse")
        self.assertEqual("shared_upstream", response.source_scope)
        self.assertGreaterEqual(len(response.lineage["compatible_upstream_sources"]), 2)
        self.assertEqual("unit_fill_rate", response.lineage["canonical_metric"])

    def test_local_enrichment_is_labeled_honestly(self):
        response = self.agent.ask("Show fill rate by category")
        self.assertEqual("local_fixture_only", response.source_scope)
        self.assertEqual([], response.lineage["compatible_upstream_sources"])

    def test_release_evaluation_can_disable_runtime_latency(self):
        response = self.agent.ask("Show revenue by warehouse")
        self.assertFalse(response.latency_measured)
        self.assertEqual(0.0, response.latency_ms)


if __name__ == "__main__":
    unittest.main()
