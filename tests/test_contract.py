import unittest

from semantic_agent.contract import QueryIntent, SemanticContract


class ContractTests(unittest.TestCase):
    def test_known_metric_and_dimension_are_valid(self):
        SemanticContract().validate_intent(QueryIntent("fill_rate", "category"))

    def test_unknown_metric_is_rejected(self):
        with self.assertRaises(ValueError):
            SemanticContract().validate_intent(QueryIntent("customer_lifetime_value", "region"))


if __name__ == "__main__":
    unittest.main()

