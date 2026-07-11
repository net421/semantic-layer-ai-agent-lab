# Semantic Publication Manifest

## Published entity

| Field | Value |
|---|---|
| Entity | `shipment_order` |
| Physical source | SQLite table `orders` |
| Grain | One row per fulfilled order |
| Contract version | `1.0.0` |
| Authorized dimensions | `region`, `category`, `carrier` |
| Published metrics | `on_time_delivery_rate`, `fill_rate`, `net_revenue`, `average_lead_time_days` |
| Consumer | `GovernedAnalyticsAgent` |
| Access mode | Read-only |

## Promotion checks

Publication is accepted only when the generated source satisfies database constraints, the semantic contract loads successfully, all governed SQL passes the tool policy, all authorized eval cases produce grounded results, all prohibited cases are refused, and `make verify` exits successfully.

The exact contract used during execution is copied to `artifacts/semantic_catalog_snapshot.json`; its SHA-256 is recorded in `artifacts/artifact_manifest.json`.
