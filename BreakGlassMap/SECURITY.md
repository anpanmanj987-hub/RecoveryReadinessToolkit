# Security policy and threat boundary

## What the application does not do

BreakGlassMap does not authenticate to your infrastructure, execute recovery actions, fetch runbooks, retrieve credentials, inspect a live network, or contact an LLM. Initial resources and exercise records are user declarations, not observed ground truth.

The browser bundle contains no external assets, telemetry or network client. Its content-security policy allows only the bundled script/style hashes and blocks connections. The optional server is read-only, loopback-only, allowlists the HTML routes and verifies Host headers. The CLI reads files explicitly selected by the caller and writes only explicitly requested outputs.

## Data handling

Never enter passwords, private keys, tokens, recovery codes or live session data. Credential **retrieval conditions** are the intended input, not their secret values. The application cannot reliably recognize every secret embedded in free text; users must keep them out.

Topology, emergency-access design, key locations and owner details may themselves be sensitive. JSON/HTML/CSV exports and optional localStorage are unencrypted. Default storage is memory-only. localStorage is not access control, durable backup, or a credential vault. Browser extensions and other software on the same device remain outside the trust boundary. A same-origin page could access localStorage, so do not co-host with untrusted pages. A file URL's storage behavior is browser-dependent.

Disabling browser persistence removes this application's keys; it does not erase copies, downloaded reports, backups, screenshots or browser/system forensic remnants. The CLI uses restrictive output-file mode on supporting operating systems, but that is not a cross-platform ACL guarantee.

## Untrusted model input

JSON only, strict field validation, bounded input size/depth/references/nodes, reference checks, duplicate checks and transactional imports. Text is escaped in HTML and SVG; no user HTML or SVG is accepted. CSV formula-prefix neutralization is provided as defense in depth, but spreadsheet applications differ: import as text and review any sensitive exports before opening them in another tool.

The condition fingerprint is FNV-1a-64, used only for accidental change detection. It is not collision-resistant against an adversary, a signature, approval authority or authentication. Anyone editing an input file can forge both a record and its fingerprint. A current record means only that its self-reported fields, date, scenario and fingerprint match the current input. Evidence file contents are never fetched or verified.

## Vulnerability reporting

Before publicly hosting the repository, enable private vulnerability reporting and define a maintainer contact. No private reporting endpoint or mailbox has been established by this source delivery. Do not invent an address or send sensitive findings to an unrelated account.

When a project repository's private reporting channel is available, report there with a sanitized reproducer and expected/actual behavior. Until then, contact the actual repository owner privately. Do not put production models, exploit payloads targeting third parties, credentials or customer identifiers in public issues. Outcome misclassification is security-relevant even without code execution.

## Supported status

v0.1.0-alpha.1 is an early alpha. No service-level commitment, external audit or production assurance is provided. Review supported runtimes, bundled code and pinned CI actions before deployment/publication. Do not weaken enterprise browser controls to run the demo.
