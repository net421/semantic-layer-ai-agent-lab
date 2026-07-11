.PHONY: run test integrations verify-artifacts reproducibility verify verify-live clean

PYTHON ?= python

run:
	PYTHONPATH=src $(PYTHON) -m semantic_agent.pipeline

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

integrations:
	PYTHONPATH=src $(PYTHON) -m semantic_agent.upstream_check

verify-artifacts:
	PYTHONPATH=src $(PYTHON) -m semantic_agent.verify_artifacts

reproducibility:
	PYTHONPATH=src $(PYTHON) scripts/verify_reproducibility.py

verify: clean integrations run test verify-artifacts reproducibility

verify-live: verify
	@test -n "$(DBT_ROOT)" || (echo "DBT_ROOT is required" && exit 1)
	@test -n "$(WAREHOUSE_ROOT)" || (echo "WAREHOUSE_ROOT is required" && exit 1)
	PYTHONPATH=src $(PYTHON) -m semantic_agent.upstream_check \
		--dbt-root "$(DBT_ROOT)" \
		--warehouse-root "$(WAREHOUSE_ROOT)" \
		--output artifacts/live_upstream_validation.json

clean:
	rm -f data/raw/orders.csv data/processed/analytics.db
	rm -f artifacts/*.json artifacts/*.jsonl artifacts/*.md
