# Build ledger

- 2026-10-13: User selected the independent BreakGlassMap implementation. Earlier chat design used as the approved functional direction. Local implementation only; no GitHub publication authorized.
- Ruling: Native JS instead of a framework, to deliver a truly standalone offline HTML and no package installation. JSON first; YAML deferred to avoid introducing a parser dependency.
- Ruling: Explicit scenario losses persist for the modeled exercise. Restoration is modeled as an action, preventing a failed seed from silently becoming healthy.
- Ruling: Storage off by default. File exports and opt-in storage are unencrypted; UI and docs warn of topology sensitivity.
- Interfaces: schema -> engine: validated model; engine -> report/UI/CLI: analyze(model, scenarioId|object, {asOf}) -> analysis. Reports take model+analysis without re-evaluation.
- Task 1: initial schema/engine suite RED 37 failing + 1 nonmutation contract, then GREEN 38/38. Implemented deterministic two-bound closure, SCC explanations, evidence separation.
- Task 2: reports/CLI suite RED 15/15, then GREEN full 53/53. Added output-file no-clobber semantics, escaped HTML, formula-neutralized CSV, explicit exit gates.
- Task 3: Single-file UI built and rendered in Chromium. Managed Chromium blocks ALL navigation (including file and loopback URLs); no policies were changed. Browser harness therefore injected the complete HTML into an opaque document and explicitly used a test-only storage double. Native storage-denied behavior was separately verified. This is not claimed as native file/HTTP E2E verification.
- Fix: Form controls named `id` shadowed form.id, bypassing the submit handler. Reproduced actual form property type, switched to getAttribute('id'), and reran CRUD/scenario browser tests.
- Fix: Browser storage unavailable initially showed an inappropriate corrupt-save error. It now disables persistence gracefully without corrupting or discarding the in-memory model.
- Improvement: Current-looking exercise records could survive a change to an existing scenario ID. Added explicit non-cryptographic condition binding; changed/unbound records are not current. 8 fingerprint tests include scope changes and structural changes, with red/green evidence.
- Verification: 500 generated small models compared against an independent exhaustive fixed-point oracle (both uncertainty bounds), not merely against another invocation of the production solver.
- Fix: Windows CRLF input could produce CSP hashes different from the browser's normalized script/style text. Red reproduction built a CRLF copy, then build normalization made it byte-identical to LF output.
- Review: Self-review only; no independent agent/human reviewer was available. No GitHub repository, live site or npm package was created.

- Fix: A malformed HTTP request target could raise an uncaught URL parser exception. A child-server regression reproduced a connection reset; the server now returns 400 and remains available. Full suite passed 79/79 afterward.
- Task 4: Added five executable fictional examples, versioned JSON Schema, English/Japanese guides, security/limits/contribution/release documents, MIT license and pinned CI configuration. Schema and all examples were validated locally.
- Verification: Final browser harness passed its documented injected-document mode; native navigation/persistence and hosted CI remain explicitly unverified. See docs/VERIFICATION.md.

- Delivery verification: source ZIP extracted separately; full 79-test suite passed, rebuilt HTML matched byte-for-byte, and all manifest entries matched. Native browser/hosted CI limitations remain unchanged.
