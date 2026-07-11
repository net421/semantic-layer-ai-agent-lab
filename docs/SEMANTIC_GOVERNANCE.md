# Semantic governance and safety

1. Only exact questions in the versioned question catalog are classified.
2. Metric aliases resolve to one canonical metric definition.
3. Ratios use ratios of additive sums rather than averages of row ratios.
4. SQL is generated from the contract, limited to 50 rows and restricted to one
   read-only relation.
5. SQLite independently denies unauthorized tables, functions and mutations.
6. Every answer records canonical metric, requested alias, dimension, source
   scope and compatible upstream sources.
7. Allowed answers reconcile against a separate Python reference calculation.
8. Recommendations are advisory and always retain `agent_executed_action=false`.
9. Customer personal data, employee scoring, raw exports, mutations and
   autonomous actions are refused.
