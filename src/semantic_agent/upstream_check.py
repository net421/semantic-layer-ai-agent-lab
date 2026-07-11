from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contract import SemanticContract
from .integration import validate_live_upstreams, validate_snapshot_contracts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate semantic bindings against pinned upstream SQL checkouts"
    )
    parser.add_argument("--dbt-root", type=Path)
    parser.add_argument("--warehouse-root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    contract = SemanticContract()
    snapshot = validate_snapshot_contracts(contract)
    if not snapshot["passed"]:
        raise SystemExit(f"Snapshot compatibility failed: {snapshot['failures']}")
    if bool(args.dbt_root) != bool(args.warehouse_root):
        raise SystemExit("Both --dbt-root and --warehouse-root are required for live validation")

    report = {"snapshot": snapshot, "live": None, "passed": snapshot["passed"]}
    if args.dbt_root and args.warehouse_root:
        live = validate_live_upstreams(contract, args.dbt_root, args.warehouse_root)
        report["live"] = live
        report["passed"] = report["passed"] and live["passed"]
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    if not report["passed"]:
        raise SystemExit("Upstream validation failed")


if __name__ == "__main__":
    main()
