# Design references

These references inform the problem framing and tooling. They do not validate this implementation, certify a model or establish the fictional demo as a real product architecture.

- Microsoft Learn, “Manage emergency access accounts in Microsoft Entra ID,” accessed 2026-10-13: https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/security-emergency-access — relevant principles include separating unnecessary recovery dependencies, strong independent authentication and periodic validation. The tool does not automatically apply product-specific configuration guidance.
- Node.js native test runner documentation, accessed 2026-10-13: https://nodejs.org/api/test.html — native test infrastructure. Actual locally exercised runtime is recorded in VERIFICATION.md.
- actions/checkout v4.2.2 release: https://github.com/actions/checkout/releases/tag/v4.2.2
- actions/setup-node v4.4.0 release: https://github.com/actions/setup-node/releases/tag/v4.4.0

The CI action versions are pinned for reproducibility, not represented as the most recent releases. Before public deployment, review supported versions and current security guidance with the actual project owner.
