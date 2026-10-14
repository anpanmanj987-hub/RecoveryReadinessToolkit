# Limits, assumptions and non-goals

## Modeling limitations

A missing node or dependency is not automatically discovered. Labeling a dependent capability as an independent available resource can produce a misleading answer. There is no traffic capture, asset discovery, IdP/PAM connector or configuration retrieval. Human review of the model is essential.

AND/OR conditions are monotone. The initial release does not model consumed/reused resources, mutual exclusion, timeouts, shifting network conditions, concurrent access limits, least privilege, credential lifecycle, token freshness, authorization quorum, negative conditions, or the security acceptability of an alternative. A credential resource means “the modeled acquisition/use conditions hold,” not “a password exists in a file.”

A route satisfying graph prerequisites may still fail in practice. Backups may be corrupt, a role may be insufficient, a procedure may be outdated, or the operators may lack skills. Represent known dependencies explicitly and use authorized practical drills to check what the model cannot determine.

Fixed-point stages are logical proof layers, not a scheduler. No elapsed recovery duration, RTO forecast, minimum cut set, optimal remediation plan or global business-risk score is computed. P1/P2/P3 group work types, not expected monetary loss.

## Evidence limitations

Records are local declarations, never independently authenticated. Matching scope/fingerprint/freshness does not validate the evidence content or prove that an entire workflow was exercised. Condition fingerprints are non-cryptographic and forgeable. Rebinding a record requires an explicit user action; only do so after a real check of the declared scope.

Metadata changes do not invalidate condition binding; all structural model changes do, including some changes unrelated to a particular node. The latter is intentionally conservative. Reference URLs are displayed as text, not followed.

## UI and platform limitations

Japanese UI only in this version. Complex Boolean expressions are editable through JSON rather than a visual nested-gate designer. The map previews 70 nodes and is a structural overview, not a complete rendering of Boolean gate semantics. Use the route inspector or full model for exact AND/OR conditions. Labels are truncated visually in map nodes; full labels are retained in tooltips, tables and exports.

Single-file browser execution is the intended distribution mode. Managed browsers may disallow file URLs, local HTTP, scripts or localStorage. Respect those policies. Test on your intended browsers before deployment. Native file navigation and native localStorage persistence could not be exercised in the build environment; see VERIFICATION.md.

No authentication, multi-user authorization, encrypted persistence, history database, live monitoring, hosted service, integrations, access revocation or credential management. Do not expose the optional server beyond loopback or repurpose it as a shared service.

## Release status

Early alpha, with automated checks and a documented self-review; no independent reviewer, external penetration test, production drill or GitHub-hosted CI execution in this delivery. The supplied CI matrix targets Linux and Windows with Node 22 and 24; none of those hosted jobs has run in this delivery. Only the local Linux environment was exercised.
