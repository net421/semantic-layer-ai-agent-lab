.PHONY: run test clean verify

run:
	PYTHONPATH=src python -m semantic_agent.pipeline

test:
	PYTHONPATH=src python -m unittest discover -s tests -v

verify: clean run test
	PYTHONPATH=src python -m semantic_agent.verify_artifacts

clean:
	rm -f data/raw/orders.csv data/processed/analytics.db artifacts/*.json artifacts/*.jsonl artifacts/*.md

