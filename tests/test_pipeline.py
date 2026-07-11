import filecmp
import json
import tempfile
import unittest
from pathlib import Path

from semantic_agent.pipeline import run_pipeline
from semantic_agent.verify_artifacts import verify_artifacts


class PipelineTests(unittest.TestCase):
    def test_pipeline_builds_complete_release_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "artifacts"
            result = run_pipeline(output, row_count=120)
            verification = verify_artifacts(output)
            evaluation = json.loads((output / "evaluation_results.json").read_text())
            compatibility = json.loads((output / "upstream_compatibility_report.json").read_text())
        self.assertEqual("pass", result["release_decision"])
        self.assertTrue(verification["passed"], verification["failures"])
        self.assertEqual(20, evaluation["case_count"])
        self.assertTrue(compatibility["passed"])

    def test_two_clean_runs_are_byte_identical(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            left = root / "left"
            right = root / "right"
            run_pipeline(left, row_count=100)
            run_pipeline(right, row_count=100)
            names = sorted(path.name for path in left.iterdir())
            self.assertEqual(names, sorted(path.name for path in right.iterdir()))
            self.assertTrue(
                all(filecmp.cmp(left / name, right / name, shallow=False) for name in names)
            )


if __name__ == "__main__":
    unittest.main()
