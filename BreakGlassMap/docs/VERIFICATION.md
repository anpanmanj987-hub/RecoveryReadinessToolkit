# Verification record — v0.1.0-alpha.1

This record describes the original 2026-10-13 archive. See the
[2026-10-14 review](REVIEW-2026-10-14.md) for subsequent fixes and native Windows
Chrome HTTP/file opening/storage verification.

**Date:** 2026-10-13. **Scope:** local source, standalone bundle, fictional examples and optional local server. This is a test execution record, not an independent audit or a production recovery certification.

## Environment

Linux container; Node.js v22.16.0; npm 10.9.2. Optional UI checks used Python 3.13.5, installed Python Playwright, and Chromium 144.0.7559.96 (Debian build). No third-party npm packages are required by the build, core tests, CLI or application.

## Automated source checks

`npm run check` builds the single-file distribution and runs `node --test`.

| Suite | Tests | Result |
|---|---:|---|
| Schema / engine contracts | 38 | Pass |
| CLI | 11 | Pass |
| Reports | 4 | Pass |
| Offline build / CSP / CRLF reproducibility | 3 | Pass |
| Condition fingerprints / evidence invalidation | 8 | Pass |
| Independent oracle / input boundaries | 5 | Pass |
| Documented example models | 5 | Pass |
| Loopback server | 5 | Pass |
| **Total** | **79** | **79 passed; 0 failed; 0 skipped** |

One oracle test generates **500 small models of seven nodes** and enumerates all Boolean assignments to find the intersection of their fixed points. It compares every node with the production solver under both uncertainty bounds. This is a separately implemented algorithm, not a separate human reviewer; the 500 models are not reported as 500 additional unit tests. The generated set is not a proof for every possible model.

The versioned JSON Schema was checked with an installed Draft 2020-12 validator, and all five bundled JSON examples validated. Runtime validation additionally checks cross-references and limits that the declarative schema does not fully express.

## Browser checks and an important environment restriction

Run: `python tests/browser-smoke.py --browser /usr/bin/chromium`.

The managed Chromium in this build environment blocks **all URL navigation**, including local HTTP and file URLs, with `ERR_BLOCKED_BY_ADMINISTRATOR`. No browser policy was disabled or changed.

The harness therefore rendered the complete generated HTML with Playwright's document-content injection in a fresh opaque browser document. This runs the actual bundled HTML, CSS and JavaScript, but is **not a native file-opening or HTTP-navigation end-to-end test**. An explicitly labeled, test-only in-memory storage double allowed the persistence logic to be exercised. The production app contains no such double. The native storage-denied path was separately exercised without the double.

Verified in that mode:

- Initial scenario, scenario switching, independent-fallback comparison and undo.
- Form editing and route addition; preservation of nested AND/OR expressions; prevention of deletion while referenced.
- Valid JSON file import, hostile labels rendered as text, malformed JSON rejected without losing the previous model.
- Exercise-record binding and invalidation after changing the same scenario's failure conditions.
- JSON download and CSV formula neutralization.
- Opt-in persistence and reload logic **with the test-only storage double**; graceful native storage denial without it.
- A 390-pixel mobile viewport without horizontal document overflow.
- No page exceptions and no external HTTP(S) requests observed during the checked flows.

The screenshots in `docs/screenshots/` are actual renders from this harness, not design mockups. The loopback HTTP server itself was separately tested using real Node HTTP requests, including invalid Host headers, mutation methods, hidden paths and malformed request targets.

## Expected fictional results

| Example | Feasible | Cannot start | Unknown |
|---|---:|---:|---:|
| identity-outage.json | 0 | 2 | 1 |
| independent-path.json | 2 | 0 | 1 |
| switch-trap.json | 0 | 1 | 0 |
| switch-prepared.json | 1 | 0 | 0 |
| empty.json | 0 | 0 | 1 |

These outcomes describe the modeled premises only. An available resource is a declaration, and a current exercise record is still a user declaration.

## Review and fixes

Review was performed by the implementer; **no independent reviewer was available**. Reproduced regressions included form `id` shadowing, unavailable browser storage, old exercise evidence surviving changed conditions, Windows line endings changing CSP hashes, and malformed HTTP request targets terminating the local server. Fixes were checked against focused regressions and the full suite.

## Not verified or not claimed

- Native opening of the HTML file or browser navigation to the local HTTP server in this restricted environment.
- Native localStorage persistence across a real browser reload on a supported file/HTTP origin.
- Windows, macOS, Safari or other browser/OS combinations. Linux/Windows + Node 22/24 CI configuration is supplied, but GitHub-hosted CI was not run.
- Independent security review, external penetration testing, production recovery drills, identity/PAM product correctness, actual permissions, recovery duration or RTO.
- Completeness of any user model, authenticity of exercise evidence, or safety of any proposed emergency-access design.

Before deploying, run the browser harness and ordinary manual file/HTTP import, export and storage checks on the intended endpoints. Respect organizational browser controls; do not weaken them to run this application.

## Packaged-artifact verification

The source ZIP was extracted to a separate temporary directory. Every entry in its SHA-256 manifest matched, `npm run check` passed all 79 tests from the extracted copy, and the rebuilt standalone HTML was byte-identical to the distributed bundle. Checksums detect file differences, not publisher authenticity; the package is not digitally signed.
