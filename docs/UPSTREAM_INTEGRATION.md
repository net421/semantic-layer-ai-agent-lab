# Upstream semantic integration

The agent remains independently executable, but its governed metrics are no
longer defined in isolation. `integrations/upstream_contracts.json` pins the
exact upstream repository commits, SQL files, Git blob identifiers, grains,
columns and formula identities reviewed for this release.

## Pinned systems

| Repository | Commit | Reviewed relations |
|---|---|---|
| `net421/dbt-analytics-engineering-lab` | `263134172e4ec3f422b47c25d01a86555ea29df9` | `fct_orders`, `mart_supply_chain_kpis` |
| `net421/cloud-warehouse-analytics-lab` | `140b076edcb89c3b27c3786887ee17d21494a44d` | `analytics.mart_order_fulfillment` |

CI checks out both repositories at those commits. The live gate recalculates
the Git blob IDs and verifies required SQL fragments, so an upstream edit cannot
silently preserve a stale semantic claim.

## Compatibility levels

- `shared_upstream`: metric and dimension exist in both the dbt and warehouse
  systems at compatible order or aggregate grains.
- `warehouse_enrichment`: the warehouse mart supplies the dimension, while dbt
  supplies the core order measures.
- `local_fixture_only`: retained only for backward-compatible local evidence and
  explicitly excluded from cross-repository claims.

## Runtime boundary

The default run creates a deterministic SQLite fixture with the same governed
column and metric contract. It does not claim that the agent is connected to a
production warehouse. The live CI gate validates source-code compatibility;
a deployment would additionally require credentials, network policy, query
routing, audit storage and production observability.
