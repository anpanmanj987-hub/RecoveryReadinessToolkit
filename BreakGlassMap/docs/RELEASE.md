# External release checklist

The local source and distributable HTML have been prepared. This document does not imply that a repository or package has been published.

Before publishing:

- Confirm repository ownership, project naming and license attribution. Name availability and trademark conflicts have not been investigated.
- Define a maintainer contact and enable a real private vulnerability reporting channel. No mailbox is invented by this package.
- Review SECURITY.md and sanitize all examples, screenshots, issues and future commits. Do not commit production models, local exports or credentials.
- Run `npm run check` on a supported Node version and run the supplied CI on the actual repository. Review pinned action versions against current upstream/security policy; references are pinned, not a claim of being the newest release.
- Test direct file opening, local HTTP if allowed, import/export, storage opt-in and mobile layout in the intended Windows/macOS browsers. Confirm the native storage boundary rather than relying only on a test double.
- Obtain an independent review of the solver, evidence binding, input boundary and offline bundle before making production-assurance claims.

The public repository can contain the root source, documentation, fictional examples, tests, `.github` metadata and committed `dist/BreakGlassMap.html`. Do not upload `.git`, private models, unrelated local files or test browser profiles.

## Suggested repository metadata

Name: `BreakGlassMap`

Description: `Find recovery dependencies that lock you out when identity, PAM or runbooks fail. Local-first AND/OR analysis, no credentials or LLM required.`

Topics: `disaster-recovery`, `business-continuity`, `break-glass`, `threat-modeling`, `identity`, `security`, `offline-first`.

Suggested first release: `v0.1.0-alpha.1`, including standalone HTML, source ZIP and SHA-256 checksums. Clearly mark alpha and link the verification/limitations documents. No live-hosted demo is provisioned by this delivery. The app may be served statically after the organization/owner approves publication of the bundled fictional sample.

## npm

`package.json` intentionally has `private: true`. Publishing to npm is a separate decision; verify package-name ownership, publication contents, provenance and supply-chain controls first. Do not tell users to run an unverified registry package with a similar name.
