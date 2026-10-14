# Model format and evaluation contract

## Minimal input

```json
{
  "schemaVersion": 1,
  "name": "Fictional recovery",
  "nodes": [
    {"id": "network", "label": "Independent network", "kind": "resource", "initial": "available"},
    {"id": "kit", "label": "Independent authentication method", "kind": "resource", "initial": "unknown"},
    {"id": "start", "label": "Start recovery", "kind": "goal", "routes": [
      {"id": "independent", "label": "Independent route", "requires": {"all": [{"ref": "network"}, {"ref": "kit"}]}}
    ]}
  ],
  "scenarios": [{"id": "baseline", "name": "Baseline", "unavailable": [], "unknown": []}]
}
```

The goal is **unknown**, not ready. Missing `initial` is unknown. Missing/empty `routes` on a derived node is a missing definition (unknown). Missing/empty scenarios creates `baseline`. At least one goal is mandatory.

Defaults apply to omitted fields. Explicit `null` values for initial states,
categories, routes, scenarios, or scenario override arrays are rejected.

## Resources vs operations

Resources are independent initial conditions. They cannot have routes. A dependency-bearing capability is an `action`, even if its label sounds like an asset (for example, “access to online runbook”). Goals and actions are derived in exactly the same way. Goals additionally participate in outcome counts and CLI gates.

Do not mark “SSO-protected runbook is available” as an independent resource when testing an SSO outage. Model `read-runbook` as an action that requires the corresponding access capability. The tool cannot detect a dependency that was never modeled.

Metadata: `category` (`identity`, `network`, `credential`, `document`, `people`, `system`, `other`), `owner`, `systemId`, `notes`, `evidence`. Categories and metadata do not change feasibility.

## Routes and expressions

Every route has `id`, `label`, and `requires`. Routes within a node are alternatives (OR). An expression has exactly one of:

- `{"ref":"node-id"}`
- `{"all":[expression, ...]}` — all children required.
- `{"any":[expression, ...]}` — at least one child required.

Empty `all` or `any`, unresolved references, duplicate node/route/scenario IDs and unsupported fields are errors. Cyclic references are intentional and permitted. The UI edits simple conjunctions with checkboxes and preserves nested expressions in a JSON editor.

IDs: 1–64 ASCII letters/digits/dots/hyphens/underscores, first character a letter or digit; `constructor`, `prototype`, `__proto__` are reserved. Labels and nonempty name fields cannot be whitespace-only. Most control characters are rejected; tabs/newlines are allowed in appropriate text and sanitized at export boundaries.

## Outage scenarios

`unavailable` and `unknown` contain node IDs and must be disjoint. An explicit override applies even to an action or goal, before route evaluation. A forced-unavailable node remains unavailable for the **entire** scenario. An unknown override means unknown in both the presence and absence of otherwise-feasible routes.

To represent restoration, create an action requiring its repair prerequisites and a separate post-repair capability. For example, `normal-login` may have a route through a healthy provider and another through `repair-provider`. Mark the healthy-provider input down; do not mark `normal-login` down unless no route can use it throughout the exercise.

The model is monotone: attaining a capability does not consume a resource or revoke another capability. Dependencies are positive, not negated.

## Two-bound least-fixed-point semantics

Let a Boolean vector represent available capabilities. For each uncertainty interpretation, evaluate the monotone model to its least fixed point.

1. Lower bound seeds only declared available resources. Forced unknowns and absent derived definitions are not seeds.
2. Upper bound also permits unknown resources, unknown overrides and absent derived definitions.
3. A derived node becomes available when any route is satisfied.
4. Forced-unavailable nodes are false in both bounds.

Lower true means `ready`; only upper true means `unknown`; neither means `blocked`. Pure cycles have no initiating seed and cannot bootstrap. An independent available route unlocks a cycle; an unknown independent entry gives uncertainty, not definite feasibility.

Synchronous rounds give reproducible witness stages. Every dependency in a ready witness belongs to an earlier stage. These stages are logical prerequisite layers, **not elapsed time or an operational execution schedule**. A selected witness is one valid route, not necessarily the cheapest or best route.

Structural strongly connected components are reported separately. An SCC may be resolved through an alternative; SCC membership by itself is not a failure verdict. Explanations follow unresolved branches; impossible branches of an otherwise-unknown OR are not blamed as the sole cause.

## Exercise evidence

Example:

```json
{
  "status": "passed",
  "checkedAt": "2026-10-12",
  "reviewer": "Fictional reviewer",
  "reference": "EXERCISE-001",
  "scope": "identity-outage",
  "maxAgeDays": 90,
  "notes": "Describe exactly which action and failure conditions were checked."
}
```

`status` is `not-tested`, `passed`, or `failed`. Passed/failed require a valid date, reviewer, reference and scope. This raw example is **unbound** until deliberately linked to a particular structural model and scenario using a `conditionHash`.

Programmatic binding (only for a record that was genuinely confirmed):

```js
import { validateModel } from './src/schema.mjs';
import { conditionFingerprint } from './src/fingerprint.mjs';
const model = validateModel(input);
const scenario = model.scenarios.find(s => s.id === 'identity-outage');
if (!scenario) throw new Error('Unknown scenario');
model.nodes.find(n => n.id === 'your-node').evidence.conditionHash =
  conditionFingerprint(model, scenario);
```

The fingerprint includes all node IDs, kinds, initial states, route IDs/conditions and the selected scenario's ID/overrides. Name/owner/notes/evidence are excluded. Node/route order is normalized. Expression-child order is preserved; reordering an equivalent expression may conservatively require revalidation. Even unrelated structural changes can invalidate a record because the entire model is included.

The format is `bgm1-` followed by 16 hexadecimal digits, computed using **non-cryptographic FNV-1a-64**. It detects accidental changes, not hostile tampering. Records and fingerprints are editable declarations and cannot establish authority.

Evidence status is evaluated separately from feasibility: untested, future, failed, other-scenario, stale, unbound, changed conditions, or current self-reported record. At exactly `maxAgeDays` the record remains within the configured window; after that it is stale. A failed record is flagged even if its old scope differs. Changing an as-of date changes the freshness assessment, not the fact that a real test occurred.

## Limits and validation

1 MiB UTF-8 JSON input, 250 nodes, 32 scenarios, 16 routes/node, 8,000 reference occurrences, depth 12 and at most 250 children per expression. UI graph preview: 70 nodes; analysis and table: all valid nodes. The JSON Schema in `schemas/model.schema.json` supplies editor assistance; **the runtime validator is authoritative** for graph-wide constraints, depth/size, duplicate IDs, reference existence and date correctness. There is no remote schema fetch in the app.

## Analysis output

`analyze(model, scenarioIdOrObject?, {asOf?})` returns version, model name, selected scenario, as-of date, condition fingerprint, goal summary, per-node statuses, witness/possibleWitness, route details, SCCs, a deduplicated checklist and explicit limitations. It performs no I/O and does not mutate input.

`ready` and `current` describe only this model and declared record; neither is a security certification. Do not infer a successful end-to-end recovery from node-level exercise records.
