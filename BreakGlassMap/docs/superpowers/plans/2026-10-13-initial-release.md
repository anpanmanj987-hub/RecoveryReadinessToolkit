# BreakGlassMap Initial Release Implementation Plan

> Execute inline in this session, with red/green tests and verification before completion.

**Goal:** Ship an independently runnable local-first OSS alpha with source, offline UI, CLI, examples, tests, and documentation.
**Architecture:** Validated JSON -> pure deterministic AND/OR fixed-point engine -> reports/UI/CLI. One shared engine across surfaces.
**Tech Stack:** JavaScript ES modules, Node.js 22+, HTML/CSS, native test runner. Zero required package dependencies.
**Spec:** ../specs/2026-10-13-breakglassmap-design.md

## Global constraints
No external publication, real credentials, target access, network scanning, LLM calls or implicit persistence. 1 MiB JSON, 250 nodes, 8,000 refs, 16 routes, depth 12. Three-valued feasibility separate from exercise evidence. MIT alpha.

## Review focus
- Unknown or malformed inputs never become successful readiness.
- OR alternatives can bypass cycles; pure cycles cannot bootstrap.
- Outage/unknown overrides take priority and stale evidence is visible.
- Untrusted labels cannot become HTML, executable content or CSV formulas.
- Scenario/model edits cannot leave stale results or silently lose nested expressions.

## Tasks
- [x] 1. Schema + engine. Files src/schema.mjs, src/engine.mjs, tests/engine.test.mjs. First write failing contract tests; implement validateModel, parseModel, analyze; run node --test. Independent closure oracle and boundary tests. Commit.
- [x] 2. Reports + CLI. Files src/report.mjs, bin/breakglassmap.mjs, tests/report.test.mjs, tests/cli.test.mjs. Test escaping, formula neutralization, explicit uncertainty, output parity, codes and invalid arguments before implementation. Commit.
- [x] 3. Offline browser product. Files src/ui.mjs, src/demo.mjs, web/template.html, web/style.css, scripts/build.mjs, tests/browser-smoke.py. Write UI smoke expectations first, build and verify in Chromium including imports and CRUD. Native file URL validation was blocked by managed-browser policy; document-injection tests are explicitly not a substitute for that acceptance check. Commit.
- [x] 4. OSS delivery. English/Japanese README, model reference, security/limits, contribution guide, MIT, changelog, CI, examples, schema, checksums. Full suite, security review, responsive screenshots, ZIP extraction rerun. Commit and package without .git or sensitive test fixtures.
