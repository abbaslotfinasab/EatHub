# ADR-ARCH-06D — Identity Provider Bake-off Plan

- **Status:** Proposed evaluation plan; no provider selected
- **Date:** 2026-11-25
- **Baseline:** `develop` after PR #255 (merge commit `0e299f4420d3216e9b55dc62ff0de7fff148106a`)
- **Scope:** Evaluate OAuth/OIDC authorization infrastructure for EatHub's ChatGPT custom MCP app and Claude Remote MCP integration
- **Non-goals:** Provider migration, production credentials, account creation, OAuth runtime, DNS changes, data migration or deployment

## 1. Decision to be made

Choose whether EatHub should:
1. Use a managed authorization service while retaining the existing EatHub account and membership system;
2. Operate a self-hosted authorization service;
3. Build and operate an EatHub-owned OAuth authorization server; or
4. Use a hybrid arrangement with an existing identity system as the authentication source of truth and a separate OAuth authorization layer for MCP clients.

No vendor is approved by this ADR. The evaluation must establish protocol compatibility, account continuity, tenant authorization, operational ownership, legal eligibility and reachability before a decision.

## 2. Existing EatHub constraints

The current application is not a blank-slate identity project:

- The canonical principal is the existing `accounts.User`.
- Business access is represented by active `Membership` records and roles.
- Membership is unique per user/business and is resolved server-side.
- Current DRF authentication uses SimpleJWT; access tokens are short-lived and refresh tokens are rotated/blacklisted.
- Existing login/register endpoints issue EatHub JWTs; they are not an OAuth authorization server for third-party MCP clients.
- Multi-business users need explicit business selection/context, but a client-supplied business identifier is never authorization evidence.
- The existing user ID and active membership graph must remain authoritative. Do not silently create duplicate EatHub users or auto-link identities by email/phone.
- Revoking an EatHub session or disabling a membership must immediately prevent new MCP tool actions through live authorization checks, even if an external OAuth token has not expired.

The target architecture is modular monolith. Provider integration belongs behind an adapter/authorization boundary and must not introduce a parallel tenant or permission model.

## 3. Candidate set

The following candidates are included for evidence-based evaluation, not as endorsements.

| Candidate | Deployment model | Evidence to investigate | Initial concern |
|---|---|---|---|
| WorkOS AuthKit / Connect | Managed SaaS | MCP-specific authorization, CIMD/DCR, resource indicators, Standalone Connect for an existing login system | Regional availability, account eligibility, contractual terms, vendor dependency, token revocation synchronization |
| ZITADEL | Managed cloud or self-hosted | OIDC, DCR, self-hosting, custom domain and deployment control | Current DCR documentation says RFC 8707 resource parameter is accepted but ignored for DCR-issued clients; verify current behavior and CIMD compatibility |
| Keycloak | Self-hosted | OIDC layers, client registration, token revocation, operational control | MCP-specific CIMD/metadata compatibility may need custom integration; operations, upgrades and high availability become EatHub responsibility |
| Auth0 | Managed SaaS | OAuth/OIDC, MCP client registration and current CIMD support | Verify exact tenant/region/product feature availability, commercial eligibility and Iran-facing reachability |

### Evidence baseline

- WorkOS documents MCP authorization using AuthKit, authorization-server metadata, PKCE S256, CIMD/DCR, resource indicators and Standalone Connect for applications with an existing authentication system. Its Standalone flow calls the existing login system and then completes the OAuth transaction with AuthKit. The documented flow also states that revoking a session in the existing authentication system does not automatically revoke a Connect authorization; EatHub must account for that gap. Sources:
  - https://workos.com/docs/authkit/mcp
  - https://workos.com/docs/authkit/connect/standalone
  - https://workos.com/docs/authkit/connect/token-claims
- ZITADEL documents RFC 7591 DCR and a configurable open-registration mode. Its current DCR limitations state that the RFC 8707 resource parameter is accepted but ignored and that dynamically registered clients share an audience. Do not rely on audience alone to distinguish these clients. Source:
  - https://zitadel.com/docs/guides/integrate/dynamic-client-registration
- Keycloak documents OIDC endpoints, dynamic client registration and token revocation. The evaluation must prove the exact MCP client discovery and registration behavior, rather than assuming generic OIDC support is sufficient. Source:
  - https://www.keycloak.org/securing-apps/oidc-layers
- Auth0 published a current MCP CIMD implementation article. Treat it as a candidate signal only; validate the feature against current product documentation and an actual tenant before scoring it as supported. Source:
  - https://auth0.com/blog/registering-mcp-clients-with-cimd-in-auth0/

## 4. Non-negotiable protocol gates

A candidate must pass every applicable gate for both target platforms:

1. OAuth 2.1 Authorization Code flow with PKCE S256 for public clients.
2. Correct authorization-server metadata and Protected Resource Metadata discovery for the deployed MCP resource.
3. Correct issuer identification (RFC 9207) and strict issuer validation.
4. Resource/audience binding: tokens for EatHub MCP must be minted for the exact EatHub MCP resource and rejected by other EatHub APIs unless an explicit, separately validated token exchange is used.
5. CIMD support compatible with the current ChatGPT custom MCP app flow; DCR support may be retained as a compatibility path where needed, but open registration must be threat-modeled and rate-limited.
6. Exact redirect URI validation, state/nonce validation as applicable, authorization-code single use, PKCE enforcement and safe refresh-token rotation.
7. Access-token signature, issuer, audience, expiry, not-before, authorized party/client and scope validation.
8. Revocation and disablement behavior documented and tested, including user logout, account suspension, membership removal and consent withdrawal.
9. No implicit trust in email, phone, client-provided tenant IDs, business IDs, customer IDs, model-generated actor claims or token custom claims as a substitute for live EatHub authorization.
10. Separate end-to-end proof for ChatGPT and Claude. Do not assume a generic OAuth/OIDC demo proves either platform's exact flow.

A candidate that cannot satisfy resource binding or the platform's current MCP OAuth contract is disqualified or requires an explicitly accepted compensating architecture decision before proceeding.

## 5. EatHub identity and tenant integration gates

- Preserve `accounts.User` as the canonical EatHub principal unless a separately approved migration decision says otherwise.
- External provider subject identifiers must be stored as an explicit, unique, issuer-scoped identity mapping. Never use email or phone as the stable key.
- Identity linking requires an authenticated EatHub session plus a verified linking ceremony; conflicting or duplicate mappings fail closed.
- Membership, active status, role, customer ownership and domain permission are resolved from EatHub on every tool invocation.
- Business selection is explicit and server-validated. OAuth scopes are coarse grants, not a replacement for live permission checks.
- A token may identify the authenticated subject and granted consent; it must not carry a trusted business authorization decision that outlives current membership.
- Define immediate denial behavior for disabled users, revoked membership, removed roles and customer ownership changes.
- Provider failure must not block ordinary EatHub login, ordering or restaurant operations.
- Do not migrate existing passwords or change the existing login flow during the bake-off.

## 6. Iran-facing reachability and legal eligibility gate

This is a hard decision gate, not a nice-to-have.

For each managed provider, obtain written answers from the vendor/legal team before any account creation or production dependency:

- Is EatHub, its operator, and the intended business activity eligible under the provider's current sanctions/export-control and acceptable-use policies?
- Are users physically located in Iran permitted to authenticate and use the service? Are there restrictions by country, IP location, residency, ownership or payment origin?
- Can EatHub lawfully purchase the service and pay invoices using its actual legal entity and payment method?
- Which service regions, data residency options, subprocessors and support locations apply?
- Are API endpoints, login pages, JWKS, metadata and token endpoints reachable reliably from common Iranian mobile and fixed networks?
- What happens during regional outages, provider policy changes or account suspension?
- Is there a documented and contractually acceptable support and incident path?

Do not evade sanctions, misrepresent location or identity, or use covert routing to bypass provider restrictions. A provider with unclear eligibility is **unqualified**, not assumed available.

For self-hosted candidates, test the operator's legal right to download, license, update and operate the software and its dependencies. Self-hosting reduces dependence on a hosted identity control plane but does not automatically resolve sanctions, lawful payment, software supply-chain or user reachability issues.

Network testing must be performed from representative Iranian mobile and fixed networks with consent and lawful methods. Measure DNS, TLS handshake, metadata discovery, authorization redirect, login, token exchange, JWKS retrieval, refresh and revocation—not just whether the homepage opens.

## 7. Weighted scorecard

Score each qualified candidate from 0 to 5 per category. A hard-gate failure overrides the weighted score and disqualifies the candidate until resolved.

| Category | Weight | What earns a high score |
|---|---:|---|
| ChatGPT MCP OAuth compatibility | 15 | Verified current CIMD/PKCE/metadata/resource/issuer flow |
| Claude Remote MCP compatibility | 15 | Verified current Claude connector flow, token lifecycle and refresh/revocation |
| Existing EatHub identity continuity | 15 | Preserves current users/login and supports safe issuer-scoped identity mapping |
| Tenant and permission security | 15 | Strong resource binding, revocation controls, no stale tenant authorization |
| Iran legal eligibility and reachability | 20 | Written vendor eligibility plus successful lawful network tests from target networks |
| Reliability and operational control | 8 | SLA, recovery, monitoring, outage isolation and exportability |
| Cost and commercial feasibility | 5 | Predictable total cost, payment feasibility and acceptable contract |
| Operational complexity and lock-in | 7 | Manageable upgrades, support, portability and exit plan |
| **Total** | **100** | |

Scoring formula: `sum(weight × score / 5)`. Do not award points for undocumented assumptions. Mark unknown evidence as **Unverified**, not as a neutral score. A candidate cannot be selected while the Iran legal eligibility/reachability gate or either platform compatibility gate remains unverified.

## 8. Proof-of-concept plan

Run the same test suite against each candidate in isolated non-production environments using synthetic accounts and data.

### Phase 1 — Protocol conformance

- Discover `/.well-known/oauth-protected-resource` and authorization-server metadata.
- Verify issuer, authorization endpoint, token endpoint, JWKS, supported grants and PKCE S256.
- Run CIMD with the exact current ChatGPT client metadata flow; separately test DCR only where required.
- Complete authorization-code flow, reject wrong redirect URI, missing/incorrect PKCE, replayed code, wrong issuer, wrong audience, expired token and wrong client.
- Verify refresh rotation, replay detection, revocation and key rotation.

### Phase 2 — Claude and ChatGPT platform tests

- Connect a development ChatGPT custom MCP app and verify consent, discovery, token audience and tool invocation.
- Connect a development Claude Remote MCP/Connector and verify the documented bearer-token handoff and refresh ownership.
- Verify disconnect/reconnect and revoked access behavior independently for each platform.
- Capture sanitized traces only; never record raw access/refresh tokens or user secrets.

### Phase 3 — EatHub account continuity

- Sign in through the existing EatHub account.
- Link the external identity only after an authenticated, verified ceremony.
- Verify the provider subject maps to exactly one EatHub principal.
- Test same email/different subject, changed email, duplicate identity, disabled user, removed membership and multi-business membership.
- Verify every tool call re-resolves active membership and domain permission from EatHub.

### Phase 4 — Network, operations and commercial review

- Obtain written eligibility and regional processing answers.
- Measure the full OAuth transaction from representative Iranian mobile and fixed networks and from at least one non-Iran control network.
- Test endpoint reachability, latency, intermittent loss, DNS/TLS failure, provider outage and fail-closed behavior.
- Compare total operating cost, support SLA, backup/restore, key rotation, upgrades and exit/export process.
- Record evidence, date, test environment and owner for every score.

## 9. Initial hypotheses (not decisions)

- **WorkOS AuthKit** is the strongest managed candidate to test first because its published MCP guide covers CIMD, DCR, resource indicators and a path for preserving an existing login system. Its session/authorization revocation boundary and Iran eligibility must be proven before it can be selected.
- **ZITADEL** is the first candidate for a managed-vs-self-hosted comparison because it offers both deployment models. Its current DCR audience/resource limitations must be resolved for the exact MCP flow.
- **Keycloak** is the control candidate for maximum infrastructure ownership, with a higher expected operational burden and a required proof of current ChatGPT CIMD compatibility.
- **Auth0** remains a managed comparator because of its published MCP CIMD work; exact product availability and eligibility remain unverified.

These hypotheses are for ordering the PoC only. They are not vendor recommendations or approval to create accounts.

## 10. Exit criteria and decision record

The bake-off is complete only when:

1. All hard gates are either passed with evidence or the candidate is disqualified.
2. ChatGPT and Claude end-to-end flows pass independently.
3. Existing EatHub identity continuity and live tenant authorization pass negative tests.
4. Iran legal eligibility and network reachability are documented for any managed candidate.
5. Weighted scores are completed with evidence and unknowns clearly marked.
6. Total cost, operational ownership, outage behavior and exit strategy are reviewed.
7. Product, engineering, security and legal/privacy owners approve the selected architecture.

The final decision must be recorded in a separate ADR amendment or decision ADR. Only after that approval may a dedicated implementation plan be opened.

## 11. Explicitly out of scope

This bake-off does not authorize:
- Production provider accounts, secrets, credentials or DNS changes.
- Replacing SimpleJWT or changing existing login/register endpoints.
- Password migration or user-table changes.
- Automatically linking users by email/phone.
- Trusting provider claims for business membership or permissions.
- Enabling AI data processing or storing prompts.
- Deploying a public MCP endpoint.
- Changes to `main` or `production`.

