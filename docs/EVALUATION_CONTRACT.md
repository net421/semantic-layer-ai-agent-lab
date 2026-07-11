# Groundedness and Correctness Evaluation Contract

| Dimension | Check |
|---|---|
| Scope correctness | Only exact authorized questions reach planning |
| Metric correctness | Returned metric equals the eval case metric |
| Dimension correctness | Returned grouping equals the eval case dimension |
| SQL correctness | SQL is generated from the versioned semantic expression |
| Result correctness | Authorized cases return at least one database row |
| Groundedness | Response retains the executed SQL, rows and contract version |
| Refusal correctness | Out-of-contract cases return no SQL and no rows |

Release thresholds are 100% for the eight checked cases. This threshold applies to the closed evaluation set and is not a claim of universal correctness.

