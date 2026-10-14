# BreakGlassMap v0.1.0-alpha.1 — design

## Intent
An independent, MIT-licensed, local-first open-source tabletop tool. Given a modeled outage, show whether recovery work can start, what blocks it, and what remains unknown. Intended for operations, security governance, and IT-BCP workshops. Do not execute recovery, store credentials, scan networks, claim actual recoverability, or publish to an external account.

## Scope and architecture
Zero runtime/development package dependencies for build, tests and CLI. Native JavaScript ES modules; Node.js >=22 for tooling. Browser distribution is one self-contained HTML file (no installation or server required). Japanese UI, English README plus Japanese guide. Input is strictly validated versioned JSON; no YAML in the initial release. Runtime input limit 1 MiB, 250 nodes, 8,000 reference occurrences, 16 routes/node, expression depth 12. All imports transactional, all dynamic strings escaped/textContent; no eval, network calls, executable user content or automatic persistence. Optional browser localStorage is explicit opt-in and unencrypted.

## Model
A resource has initial available/unavailable/unknown and no routes. An action or goal has routes; each is an alternative (OR). A route's nonempty requires expression is a ref, all, or any. Empty route lists for a derived node mean definition missing (unknown), not safe. AND/OR nesting is supported. Metadata includes owner, systemId, category, notes, and optional evidence (status not-tested/passed/failed, date, reviewer, reference, scope, maxAgeDays). Scenario unavailable/unknown lists override a node; overlaps or unknown IDs are rejected. A forced unavailable node remains unavailable for the entire scenario. Model service restoration as a separate action/capability with routes, never silently restore a failed resource.

## Evaluation
Two monotone least-fixed-point evaluations. Lower seeds only declared available resources; upper also seeds unknown resources/undefined derived nodes. Actions derive when one route evaluates true. Forced unavailable is false in both. Lower=true => ready (model feasible), upper-only=true => unknown, otherwise blocked. Pure unseeded cycles are blocked in both; unknown external entry yields unknown; available independent alternative unlocks the cycle. Witness levels are computed in synchronous rounds to avoid circular explanations. Ready witness steps are strictly earlier than their dependents. Evidence never silently changes modeled facts or makes feasibility a successful drill.

Return exact scenario, as-of date, statuses, selected witness routes, dependency details, structural strongly connected components, affected unfinished goals and a deduplicated checklist. Cycles alone never imply blockage. Evidence freshness is reported separately; expired/future/failed records are not represented as successful current validation. Reports retain input assumptions and limitations.

## Browser flows
Fictional demo starts with identity provider outage and circular PAM/credential/runbook dependencies. Three goals show blocked/unknown separately. Select preset scenario or individual failed resources. An explicit what-if button prepares independent local kit/runbook and shows comparison, without changing evidence. Tabs: overview/map, model editor, checklist, guide. Select a node to inspect routes, owners and evidence. Form-based editor can add/edit/delete nodes, routes via prerequisite checkboxes (OR between routes, AND within a route); nested JSON expressions remain supported through JSON editor and never silently flattened. Add/edit scenarios, JSON import/export, CSV and HTML reports. No passwords, real organization data or attached files are bundled.

## Acceptance and exclusions
Engine cases: AND, OR, nesting, pure/self cycles, unknown external entry, escape path, forced outage priority, permutation invariance, missing definitions, invalid input, caps, witness order, stale/failed evidence. Compare against independent exhaustive Boolean closure solver on randomized small models. CLI: deterministic JSON/text/CSV/HTML, validate, exit codes 0 ready, 1 invalid/error, 2 blocked goal, 3 unknown goal, 4 evidence gate. Browser tests: file URL, scenario selection, what-if, CRUD, export/import, malformed/injected input, persistence off/on, narrow viewport. No external pen-test, full recovery scheduler, duration/RTO optimization, minimal cut sets, authority verification, SSO integration, or real-environment validation.

## Implemented refinements and verification boundary
Exercise records may be explicitly bound to a selected scenario and the structural model using a versioned non-cryptographic fingerprint. Metadata-only changes do not invalidate this binding; structural changes and overrides do. This is a change marker, not evidence authentication or a signature. Binding never changes modeled availability.

The optional read-only server binds to loopback, restricts Host/path/method and rejects malformed URL targets. The bundle normalizes line endings before computing CSP hashes.

Native file/HTTP browser navigation was prevented by managed-browser policy. The actual bundle was tested by document injection with an explicitly test-only storage double; native storage denial was tested separately. This is an acceptance limitation, not a claim that native navigation or native persistence passed. See docs/VERIFICATION.md.
