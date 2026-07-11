from __future__ import annotations

import filecmp
import tempfile
from pathlib import Path

from semantic_agent.pipeline import run_pipeline


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        left = root / "left"
        right = root / "right"
        run_pipeline(left)
        run_pipeline(right)
        left_files = sorted(path.name for path in left.iterdir() if path.is_file())
        right_files = sorted(path.name for path in right.iterdir() if path.is_file())
        if left_files != right_files:
            raise SystemExit("Generated file inventories differ")
        failures = [name for name in left_files if not filecmp.cmp(left / name, right / name, shallow=False)]
        if failures:
            raise SystemExit(f"Non-deterministic artifacts: {failures}")
        print(f"Reproducibility passed: {len(left_files)} byte-identical files")


if __name__ == "__main__":
    main()
