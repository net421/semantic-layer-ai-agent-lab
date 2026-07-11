# Metric Ownership Registry

| Semantic ID | Canonical definition owner | Validation owner | Consumers | Change policy |
|---|---|---|---|---|
| `on_time_delivery_rate` | Analytics Engineering | Operations Analytics | Agent, service review | Major definition changes require a contract-version increment and eval review |
| `fill_rate` | Analytics Engineering | Inventory Operations | Agent, inventory review | Numerator or denominator changes require reconciliation tests and a contract-version increment |
| `net_revenue` | Revenue Analytics | Finance Analytics | Agent, regional review | Currency or recognition changes require a new contract version |
| `average_lead_time_days` | Supply Chain Analytics | Logistics Operations | Agent, carrier review | Calendar convention changes require a new contract version |

Ownership labels describe the review roles used by this laboratory. They do not imply a real company organization or external approval.

