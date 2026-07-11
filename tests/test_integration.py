import hashlib
import tempfile
import unittest
from pathlib import Path

from semantic_agent.contract import SemanticContract
from semantic_agent.integration import git_blob_sha, validate_live_upstreams, validate_snapshot_contracts


class IntegrationTests(unittest.TestCase):
    def test_snapshot_contracts_are_compatible(self):
        report = validate_snapshot_contracts(SemanticContract())
        self.assertTrue(report["passed"], report["failures"])
        self.assertEqual(3, report["source_count"])
        self.assertEqual(24, report["metric_binding_count"])
        self.assertEqual(9, report["dimension_binding_count"])

    def test_git_blob_sha_matches_git_object_rule(self):
        content = b"select 1\n"
        expected = hashlib.sha1(b"blob 9\0" + content).hexdigest()
        self.assertEqual(expected, git_blob_sha(content))

    def test_live_validation_detects_missing_checkouts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = validate_live_upstreams(SemanticContract(), root / "dbt", root / "warehouse")
        self.assertFalse(report["passed"])
        self.assertEqual(3, report["source_count"])
        self.assertTrue(any("missing source file" in failure for failure in report["failures"]))


if __name__ == "__main__":
    unittest.main()
