# Normalized input model / schema 1.0

The runtime validator in `cleanroomcheck/model.py` is authoritative. `model.schema.json` documents structural constraints for editors. The Python validator additionally checks duplicate IDs, reference existence, semantic combinations, byte/depth/item budgets and cross-product limits. JSON Schema alone does not prove these properties.

## Root

All seven top-level sections are required. Unknown fields are rejected at every modeled object level.

| Section | Meaning | Limit |
|---|---|---|
| schema_version | Exactly `"1.0"` | — |
| project | id, name, demo; optional description | one |
| evidence | Metadata only, not attached evidence files | 0–2,000 |
| nodes | Assets, identities and administrative boundaries | 1–500 |
| edges | Directed effective relationships | 0–2,000 |
| scenarios | Explicit compromised starting nodes | 1–16 |
| assessments | Business/workload review units | 1–50 |

The assessment×scenario product must not exceed 200. Each unit produces 32 rule results, including NOT_APPLICABLE results. Files/API request bodies are bounded at 2MiB; normalized input at depth32 and 50,000 visited values. API envelopes can reach their bound slightly earlier than a bare model. IDs begin with an ASCII letter/digit and contain only ASCII letters/digits plus `_.:-`, up to80 characters.

## Evidence metadata

```json
{"id":"cfg-01","type":"configuration","collected_at":"2026-10-14","reference":"approved-design/revision-3","note":"Human reviewed the named scope"}
```

Types are `self_reported`, `configuration`, `tested`. References are inert strings: not fetched, followed, verified or embedded. A date is a calendar day, not a timestamp. Future-dated and stale evidence cannot qualify a positive result. The default90-day maximum is a local policy setting, not an external security standard.

Type strength is `tested > configuration > self_reported`. Each required fact must have qualifying metadata; evidence on one fact does not qualify another. The tool does not verify the metadata's honesty, document contents, scope, signatures or consistency with the real environment. A fact shared across scenarios must be reviewed by a human for every scenario.

## Nodes

Required: `id,label,kind,provider,plane`. Optional: `tenant,evidence,note`.

`provider`: azure / aws / m365 / generic.

`plane`: production / backup / recovery / shared. This is a descriptive grouping, not a trust proof.

`kind`: tenant / account / subscription / identity / device / pipeline / recovery / workload / backup / key / network / document / log_store / approval.

`tenant` is an optional reference to an existing tenant node for Azure/M365 nodes. It cannot refer to the node itself. A tenant node with provider azure can be the explicit Azure Global Administrator compromise boundary. No AWS Organizations power is inferred solely from a node being an account.

## Directed edges

```json
{"id":"e01","source":"prod-admin","target":"recovery-sub","relation":"controls","evidence":["cfg-01"]}
```

| relation | Semantics | Propagates administrative control? |
|---|---|---|
| controls | Source can exercise effective administrative control over target | Yes, transitively |
| can_delete | A controlled source can delete the named target | No; terminal impact only |
| can_disable | A controlled source can disable the named target | No; terminal impact only |
| network_reach | Effective allowed network connection, in the stated direction | No; evaluated as network only |
| depends_on | A recovery dependency reference | No; displayed only in alpha |

Network reachability starts from compromised nodes and their controlled nodes, then follows one or more `network_reach` edges. A control path alone is not a network path. A detected connection is not an assertion of exploit success.

Edges represent **already-resolved effective relationships**. IAM denies, SCPs, PIM activation, conditional role assumptions, firewall rules, JIT gates, time windows and approvals must be resolved by the reviewer before drawing an edge. No policy-language evaluator is included. Cycles are bounded by graph traversal visited sets.

## Scenarios

```json
{"id":"tenant-admin","name":"本番テナント全体管理者の侵害","compromised":["prod-tenant"],"azure_global_admin_tenants":["prod-tenant"]}
```

Every scenario has one or more compromised nodes. `azure_global_admin_tenants` is optional and must be a subset of initially compromised Azure tenant nodes. Only this explicit opt-in infers administrative elevation from those tenants to Azure subscriptions with the same tenant. It does not infer arbitrary rights on all M365 resources or arbitrary nodes. Scenario selection is an assumption, not a measured attack.

## Assessments and facts

Required: id,name,provider,workload,production_node,recovery_node,backup_node,facts. Optional: key_node,log_node,note.

`workload`: azure_vm / aws_ec2 / m365 / other. Azure VM/AWS EC2/M365 must match their provider. Production/recovery references can point to tenant, subscription, account, recovery or workload nodes. Backup must be a backup node; a supplied key/log must have the corresponding kind.

```json
{"independent_identity":{"value":true,"evidence":["cfg-01"]},"restore_tested":{"value":null,"evidence":[]}}
```

Each known fact is an object with `value` and optional evidence ID list. Omitted fact or null means unknown. False means explicitly not satisfied. Strings like `"true"` are not accepted as booleans. A scalar fact is not accepted. See `RULES.md` for the complete field catalogue.

Protection dates are evaluated by day. An end date on or before the review date does not qualify as protected. Numeric hours/days must be nonnegative and no greater than1,000,000; day counts are integers. A required retention of0 is treated as undefined by the retention rule, rather than evidence of safety.

## JSON / YAML / CSV interchange

JSON duplicate keys, unknown fields, nonfinite numbers, unpaired Unicode surrogates, invalid references and malformed dates fail closed. JSON integer tokens are limited to100 digits before semantic validation; actual numeric facts have the tighter bounds above. YAML requires optional PyYAML; safe loading is used, with aliases/anchors/custom tags unsupported. YAML ISO-like scalars are kept as strings for date validation.

CSV bundle comprises `structure.json` (same model with empty facts) and `facts.csv` with exactly these columns:

```csv
assessment_id,field,value_json,evidence_ids
```

`evidence_ids` is a semicolon-separated list. Duplicate rows or facts overlapping structure and CSV are errors. JSON serialization is required in value_json, including quotes around string values. Export does not package actual evidence.

## Output contract

Reports contain tool/ruleset version, as_of, max_evidence_age_days, canonical input SHA-256, frozen project/scope snapshots, findings and sources. Hashes establish reproducibility of normalized input, **not authenticity**. Result IDs are `scenario_id/assessment_id/rule_id`.

Comparison uses those stable IDs and checks project/version/date/policy compatibility. Changing compromised seeds, Azure escalation assumptions or provider/workload produces scope-change labels. The tool cannot know that the meaning of an unchanged arbitrary ID has been repurposed. Independent business/asset coverage reconciliation remains a human task.

## Extension boundary

The schema is native to CleanRoomCheck. `depends_on` aligns conceptually with recovery dependency mapping, but no BreakGlassMap adapter, AND/OR requirement model or cross-project API compatibility is implemented in this release. Add adapters as explicit versioned importers, never by claiming silent compatibility.
