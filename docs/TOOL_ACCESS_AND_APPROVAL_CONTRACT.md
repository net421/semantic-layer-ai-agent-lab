# Tool Access and Approval Contract

| Control | Enforced behavior |
|---|---|
| Database access | SQLite URI opened in read-only mode |
| Authorized table | `orders` only, enforced by a SQLite engine authorizer |
| SQL statement | One `SELECT`, no statement separator |
| Result size | Maximum 50 rows |
| Mutations | Prohibited by keyword policy and read-only connection |
| Recommendation | Investigation proposal only |
| Operational action | Never executed by the agent |
| Approval | A human must accept, reject, or request additional analysis |

The text guard is backed by `sqlite3.Connection.set_authorizer`, which denies reads from every other table and denies unapproved SQLite functions. Tests cover mutations, ordinary unauthorized tables, comma joins to the SQLite catalog and table-valued PRAGMA access. The contract intentionally favors refusal over ungrounded flexibility.
