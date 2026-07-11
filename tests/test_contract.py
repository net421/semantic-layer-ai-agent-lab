import unittest

from semantic_agent.contract import QueryIntent, SemanticContract


class ContractTests(unittest.TestCase):
    def test_known_metric_and_dimension_are_valid(self):
        SemanticContract().validate_intent(QueryIntent("fill_rate", "category"))

    def test_unknown_metric_is_rejected(self):
        with self.assertRaises(ValueError):
            SemanticContract().validate_intent(QueryIntent("customer_lifetime_value", "region"))

    def test_alias_resolves_to_canonical_metric(self):
        contract = SemanticContract()
        self.assertEqual("unit_fill_rate", contract.canonical_metric_name("fill_rate"))
        self.assertEqual("revenue", contract.canonical_metric_name("net_revenue"))

    def test_all_catalog_questions_validate(self):
        contract = SemanticContract()
        for intent in contract.questions.values():
            contract.validate_intent(intent)

    def test_lineage_intersects_metric_and_dimension_sources(self):
        contract = SemanticContract()
        intent = contract.classify("Show OTIF rate by carrier")
        lineage = contract.lineage_for(intent)
        self.assertEqual(
            ["dbt_fct_orders", "warehouse_order_fulfillment"],
            lineage["compatible_upstream_sources"],
        )


if __name__ == "__main__":
    unittest.main()
