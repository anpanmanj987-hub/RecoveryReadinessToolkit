# Contributing

Keep the project focused on a single question: can modeled recovery work begin under the selected outage?

Use fictional models only. Do not submit real credentials, customer names, topology exports, internal URLs or identifiable people. Read SECURITY.md before reporting a security-relevant outcome.

## Local workflow

Node.js 22+; no dependency installation required:

```sh
npm run build
npm test
```

Changes to the engine need a failing behavioral test before implementation. Preserve three-valued semantics, explicit AND/OR structure, the ability to bypass a cycle through an independent route, and separation of exercise evidence from modeled feasibility. The exhaustive oracle is intentionally independent of the production closure algorithm; do not rewrite it to reuse the engine.

Browser changes should run the optional Playwright harness and inspect desktop/mobile screenshots. The harness reports whether native navigation/storage or a restricted-environment renderer/storage double was used. Never describe the latter as an end-to-end native browser run.

The app is a small native-module codebase: schema -> fingerprint/engine -> report and UI/CLI. The builder supports only the repository's deliberately restricted import/export subset. Do not silently broaden it into a general JavaScript bundler. If adding a package becomes justified, document why, pin its version, add a lockfile, review its license and update the security/dependency claims.

Rebuild `dist/BreakGlassMap.html` after browser source changes. The generated file is committed to make offline distribution easy. Test both LF and CRLF builds. Keep screenshots free of real data and temporary toast overlays.

## Review expectations

State what behavior changed, the tests run, their actual outcomes, and any untested environment. Consider scope drift, stale proof records, unknown-field mistakes, circular bootstrap assumptions, malformed imports, text/HTML boundaries, CSV output and confidentiality. Never label model readiness as verified recovery.
