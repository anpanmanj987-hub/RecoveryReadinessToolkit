# CleanRoomCheck Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Deliver an offline, evidence-aware clean-room architecture review OSS.
**Architecture:** Strict normalized model -> typed graph + fixed rule catalog -> deterministic findings -> safe HTML/CSV/JSON. CLI and loopback UI share one engine.
**Tech Stack:** Python >=3.10 standard library; optional PyYAML; unittest; browser integration tests.
**Spec:** docs/superpowers/specs/2026-10-14-cleanroomcheck-design.md

## Global Constraints
No customer data, telemetry, cloud API calls, deployments or restores. No code execution from inputs. Positive results need evidence metadata, not self-attestation alone. 90-day evidence window is configurable. Alpha, not a certification. Independent directory and build/alpha branch.

## Review Focus
- A missing or stale fact must not produce PASSED: task 2 truth/evidence tests.
- Privilege must not spread across communication or dependency links: task 2 graph and differential tests.
- Hostile file/HTML/CSV input must remain inert: tasks 1 and 3 rejection/escaping tests.
- Removing an assessment must not count as fixing it: task 3 comparison tests.
- The shipped wheel and browser must use the same engine and packaged data: tasks 4/5 smoke tests.

### Task 1 — model and input adapters
**Files:** cleanroomcheck/model.py, cleanroomcheck/io.py, tests/test_model.py, tests/test_io.py
**Interfaces:** validate_model(data: dict) -> dict; load_model(path: Path) -> dict; CSV normalized bundle read/write.
- [x] Write tests for minimum model, types, duplicate IDs/keys, dangling refs, malformed dates, resource budgets and CSV round-trip.
- [x] Run tests to see missing implementation fail.
- [x] Implement strict validation and bounded JSON/YAML/CSV input.
- [x] Run full suite and commit.

### Task 2 — graph and evidence-aware rule engine
**Files:** cleanroomcheck/graph.py, cleanroomcheck/engine.py, cleanroomcheck/catalog.py, cleanroomcheck/data/sources.json, tests/test_engine.py, tests/test_graph.py
**Interfaces:** evaluate(model, as_of: date, max_evidence_age_days: int = 90) -> dict; control_paths(model, scenario) -> dict.
- [x] Test directed effective control, cycles, limited Azure inference, known bad claims, independent condition evidence, expiry, restore incompatibility and service scope.
- [x] Observe RED, implement fixed rules, source metadata and traceable findings.
- [x] Compare random graphs against independent closure; run suite and commit.

### Task 3 — reports and CLI
**Files:** cleanroomcheck/report.py, cleanroomcheck/compare.py, cleanroomcheck/cli.py, cleanroomcheck/__main__.py, tests/test_report.py, tests/test_cli.py
**Interfaces:** render_html(result) -> str; compare_results(before, after) -> dict; main(argv=None) -> int.
- [x] Test escaping, formula neutralization, change classifications, CLI exit codes and no overwrite of input.
- [x] Observe RED then implement report, questions, verification sheet, compare and CLI.
- [x] Run suite and commit.

### Task 4 — local UI and examples
**Files:** cleanroomcheck/server.py, cleanroomcheck/web/index.html, examples/*.json, tests/test_server.py, tools/browser_smoke.py
**Interfaces:** make_server(port=0) -> HTTPServer; routes /, /api/bootstrap, /api/evaluate; UI export calls same evaluator.
- [x] Test loopback Host/Origin/session token, malformed requests and shared evaluator consistency.
- [x] Implement form, local import/export, scenario/assessment editing, demo and reports. No filesystem writes from HTTP.
- [x] Browser smoke: load demo, edit fact, evaluate, export, unknown/error paths.
- [x] Run suite and commit.

### Task 5 — release and documentation
**Files:** README.md, docs/*, pyproject.toml, LICENSE, SECURITY.md, CONTRIBUTING.md, .github/workflows/tests.yml
- [x] Document semantics/limits, model, rules, reference patterns, demo assumptions, evidence collection and public release instructions.
- [x] Generate deterministic example reports; test package installation outside source tree.
- [x] Run complete suite and browser tests, inspect final outputs, record actual results, zip and hash.

Execution qualification: browser smoke completed as offline DOM/component testing plus separate real HTTP tests, not native browser HTTP end-to-end. The latter was blocked by environment policy. See docs/VERIFICATION.md. No cloud or independent reviewer verification was performed.
