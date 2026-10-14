# Security posture

This is an alpha architecture-review tool, not a security boundary or a certification service.

## Data and execution
The CLI reads explicitly named local inputs and creates new output directories. The loopback UI keeps the current model in browser memory and processes it in the local Python process; it does not persist models, send telemetry, run cloud SDKs, or deploy anything. Reports and input JSON are plaintext. The OS, browser extensions and local processes may access that data.

Do not enter credentials, personal data, private keys or real backup contents. Use aliases for sensitive asset identifiers. Evidence references are displayed as text; no referenced file or URL is automatically fetched. Official documentation hyperlinks are only followed on user action.

## Implemented defenses
Strict ID/type/reference checks, unknown-key and duplicate-key rejection, bounded input sizes, YAML safe loading without aliases, HTML escaping, hashed report scripts, CSV formula neutralization, create-only output directories, and loopback Host/Origin/session-token checks. The web server binds IPv4 127.0.0.1 only. These measures have tests, but have not had an independent security audit.

Do not expose the local web server through port forwarding, containers bound to external interfaces, a reverse proxy, or a multi-user hosting service. It is not a hardened production web application. Local-malware resistance, OS sandboxing, memory encryption and multi-user authorization are out of scope.

## Findings and evidence
The engine trusts normalized input relationships and declared evidence metadata. It does not validate evidence contents, signatures, scoping or truthfulness. A supplied configuration/test reference can be false or unrelated; human review is required. A passed rule is never evidence of a malware-free environment or a successful future recovery.

## Reporting a vulnerability
Do not put real infrastructure data or secrets in public issues. After publication, use private security reporting if enabled by the repository owner. Otherwise, open a minimal non-sensitive request for a private reporting channel. Do not upload customer models as demonstrations.
