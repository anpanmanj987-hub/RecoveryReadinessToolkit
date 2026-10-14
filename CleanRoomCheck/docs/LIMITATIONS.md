# Limits and non-goals / alpha 0.1.0a1

## What this tool proves

It deterministically applies a fixed set of design-review heuristics to **supplied model facts and evidence metadata**. A positive finding is model-level condition satisfaction, not certification of a live environment. The output must be reviewed by an accountable architect and recovery operator.

Evidence type, reference, date and applicability are user-supplied. The tool does not retrieve documents, inspect screenshots, verify cloud API output, verify signatures, detect fabricated evidence, or prove the claimed scope. Several facts are reused across scenarios; humans must confirm that the referenced evidence actually covers every scenario. Changing metadata from self_reported to tested without a real test is not a valid remediation.

## Deliberately not implemented

- Cloud API collectors, account discovery, IAM/SCP policy evaluation, inventory reconciliation.
- Terraform/Bicep/CloudFormation deployment or automatic configuration changes.
- Backup creation, irreversible lock configuration, key administration, restoration, tenant creation or network reconnection.
- Malware engines, EDR integration, clean-point detection or forensic analysis.
- Comprehensive product/version/region/workload/cryptography compatibility database.
- Complete tenant rebuild, M365 cross-tenant migration, DNS/domain or identity recovery automation.
- BreakGlassMap compatibility, dependency AND/OR semantics, minimum recovery sets or bootstrap recovery simulation.
- Multi-user authentication, company-by-company authorization, centralized persistence, encrypted storage or signed reports.

## Graph semantics and coverage

Controls are explicit effective relationships, not raw permission statements. Deny policies, role-assumption prerequisites, conditions, time windows, JIT and multi-party approvals are not solved. Only the opt-in Azure Global Administrator to same-tenant Azure subscription elevation is inferred. AWS Organizations privileges are never guessed.

The first discovered path is shown; all possible paths, minimum cuts and privilege lattices are not enumerated. An edge absence is not an absence proof. A positive absence result requires a supplied coverage-confirmed fact with adequate metadata, which still must be verified by a person. Network edges represent allowed direction and scope, not exploitability, protocol simulation or packet-level tests. Control never automatically means a network connection.

A backup management finding does not claim a locked recovery point can actually be deleted. Key survival is separately assessed. Multiple alternative backup copies/keys/restore paths should be represented as separate assessments; the alpha has no OR-of-recovery-options solver. depends_on is reference-only.

Threat scenarios are not an exhaustive attacker model. Supply tenant administrators, backup operators, shared endpoints/pipelines, credentials and other relevant entry points explicitly. The tool does not discover lateral-movement capabilities from real configurations.

## Evidence, dates and immutability

Dates use calendar days. Evaluation date defaults to the runtime's local day except fixed-date built-in demos. Evidence older than the configurable maximum or in the future cannot qualify a positive finding. The 90-day default is a tool policy, not a security standard. Stale negative inputs may still surface as suspected design deficiencies with limited assurance.

A protection end date equal to the evaluation date is conservatively treated as not sufficient. Numeric retention is compared only to a supplied business requirement. No retention duration, including5–10 business days, is automatically deemed safe against undiscovered compromise. The underlying evidence must address actual recovery points, lock applicability and finalized grace periods. An asserted locked mode alone is insufficient.

Tests-recorded fields do not independently interpret the test outcome or prove absence of malware/persistence. Business recovery, restored data integrity and clean-room exit require human sign-off.

## Comparison limits

Comparisons reject different project IDs, tool/ruleset versions, dates and evidence policies. They label seed/explicit-escalation/provider/workload changes and removals as scope changes rather than remediation. They cannot detect an arbitrary ID silently repurposed to mean a different asset, or a reviewer falsely asserting a complete graph. Node/assessment identity and coverage must be reconciled outside the tool.

A drop in findings can be caused by changed input assertions. Do not report it as a measured improvement until deployment and appropriate tests have actually occurred. The Azure improved demo deliberately leaves product support and all unperformed tests unknown.

## Local UI security

The HTTP server binds only to IPv4 loopback, checks Host/Origin, and uses a per-process request token. It rejects unsupported methods/routes, oversized JSON and invalid models. HTML escaping, CSV formula protection, static route allowlists and Content Security Policy mitigate some common presentation risks.

It is not a hardened network service. No rate limiting or process isolation is provided. A hostile process running as the same OS user can access memory/files and fetch the loopback token. Do not expose through a reverse proxy, SSH tunnel or shared desktop service. Files downloaded/saved by the user are plaintext and may expose sensitive architecture and evidence references. Do not put passwords, tokens, private keys or real customer data in the public repository or demo files. No auto-save is provided.

Reports have no external fonts/scripts. Official source hyperlinks are user-initiated navigation. Opening the report does not itself validate those sources or cloud state.

## Validation limits and release qualification

Current tests were run on Linux/Python3.13.5, with separate real HTTP tests and offline Chromium DOM/component checks. Native browser-to-loopback end-to-end navigation was blocked by an environment-wide URL policy, and was not bypassed. Offline component checks are **not** native HTTP or native file-download E2E. Windows/macOS and the CI matrix are not executed here. See VERIFICATION.md for exact final results.

No independent security review, production deployment, live cloud restore, cloud tenant teardown, customer acceptance test or vendor compatibility certification has been performed. The package name/trademark and third-party namespace availability are not checked. This is an MIT-licensed alpha to review and adapt, not a production assurance product.
