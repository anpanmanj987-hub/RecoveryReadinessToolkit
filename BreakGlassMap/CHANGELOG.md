# Changelog

## Unreleased — 2026-10-14 review

- Preserve unchanged flat route expressions during metadata edits, retaining
  their order, repeated references, and existing evidence binding.
- Reject explicit null state/category/route/scenario/override values rather than
  silently applying omitted-field defaults.
- Read UTF-8 browser artifacts explicitly in the optional Python harness on
  Windows; add native input-boundary and focused real-browser regressions.
- Rebuild the standalone app and refresh fictional screenshots/checksums. See
  [the review record](docs/REVIEW-2026-10-14.md) for actual test scope.

## 0.1.0-alpha.1 — 2026-10-13

Initial independent source distribution. Single-file local browser UI, validated JSON model, three-valued AND/OR fixed-point analysis, circular dependency explanations, independent recovery-path comparison, form-based node/route/scenario editing, exercise metadata, change-bound evidence records, JSON/CSV/HTML export, CLI outcome gates, read-only loopback server, native tests and optional browser harness.

The examples are fictional. No GitHub repository or npm package was published as part of this distribution. See docs/VERIFICATION.md for validation scope and known environment limitations.
