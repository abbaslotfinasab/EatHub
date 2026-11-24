# ARCH-06E — Identity Provider PoC Execution Runbook

- **Status:** Proposed execution procedure; no provider selected or authorized
- **Date:** 2026-11-25
- **Baseline:** `develop` after PR #256 (merge commit `2cd37a5731f2efdb16ebcd24d848d70641285581`)
- **Related decisions:** ADR-ARCH-06, ADR-ARCH-06C (OAuth/platform compatibility), ADR-ARCH-06D (provider bake-off)
- **Scope:** Repeatable, evidence-led evaluation of WorkOS AuthKit, ZITADEL, Keycloak and Auth0 for ChatGPT and Claude MCP integrations
- **Non-goals:** Production implementation, provider selection, account creation, credential issuance, real-user data processing, DNS changes, migrations or deployment

## 1. Authorization boundary

This runbook defines how an approved PoC is to be executed. It does not itself authorize external provider accounts, contracts, paid plans, credentials, network routing, or processing of personal data.

Before any external account or tenant is created, record explicit approval from the product owner and security/privacy owner, and obtain written provider eligibility answers for the actual operator, entity, intended activity, payment method and users in relevant countries. Legal review must determine whether the proposed use is permitted. An unknown answer is a stop condition, not an assumption of permission.

No sanctions, geographic, identity, payment or provider restrictions may be evaded. Do not misrepresent location or ownership, use another party's account, or introduce covert proxies/tunnels. Network measurements must use lawful, transparent connectivity from consenting testers and representative networks.

Until those approvals exist, work is limited to public documentation review, local protocol fixtures, synthetic test design and this runbook.

## 2. Candidate and environment matrix

| Candidate | Mode under test | Entry condition | Explicit proof required |
|---|---|---|---|
| WorkOS AuthKit / Connect | Managed | Written eligibility, region and commercial answers | ChatGPT CIMD/resource flow; Claude bearer-token flow; identity handoff and revocation boundary |
| ZITADEL | Managed and/or self-hosted, evaluated separately | For managed: written eligibility; for self-hosted: license, supply-chain and operating review | Resource/audience isolation, DCR/CIMD behavior, token validation and both platform flows |
| Keycloak | Self-hosted | Approved lawful hosting, software distribution and operations plan | Exact ChatGPT CIMD/metadata compatibility, Claude flow, HA/key rotation/revocation operations |
| Auth0 | Managed | Written eligibility, tenant/region/product and commercial answers | Current tenant feature support, ChatGPT CIMD and Claude flow, token lifecycle |

A managed and self-hosted deployment of the same product are separate candidates with separate evidence and scores. Do not transfer a result from one mode to the other.

## 3. Pre-flight checklist

The PoC owner must complete and attach evidence for every item before issuing credentials:

- [ ] Product owner approves the bounded PoC objective, participants and end date.
- [ ] Security/privacy owner approves the threat model, synthetic data plan and evidence handling.
- [ ] Legal/commercial owner records provider eligibility, sanctions/export-control, payment and contract conclusions.
- [ ] Provider confirms supported service regions, data residency, subprocessors and support location in writing.
- [ ] Network test method is lawful, transparent and consented; no circumvention or misrepresentation.
- [ ] Isolated non-production environment and separate test tenant are identified.
- [ ] Synthetic users, businesses, memberships and orders are generated; no production customer or restaurant data is copied.
- [ ] Secret manager and short-lived test credentials are approved; no secrets in source control, tickets, screenshots or logs.
- [ ] Named owners exist for test execution, evidence review, security sign-off and cleanup.
- [ ] Expiry date and deletion/closure procedure for all test accounts, tokens and test data are recorded.

Any unchecked item blocks provider onboarding and live endpoint testing.

## 4. Standard test identities and tenant fixtures

Use stable synthetic fixtures across candidates:

| Fixture | Expected state | Purpose |
|---|---|---|
| U-CUSTOMER-A | Active customer | Customer-owned order reads and permitted actions |
| U-OWNER-A | Active owner of Business A | Owner tools scoped to Business A |
| U-STAFF-A | Active staff with limited role in Business A | Role-based denial/allowance |
| U-OWNER-B | Active owner of Business B only | Cross-tenant isolation |
| U-MULTI | Active memberships in A and B | Explicit business selection and context switching |
| U-DISABLED | EatHub account disabled | Immediate denial |
| U-REVOKED | Active user, membership revoked during test | Live authorization and revocation |
| U-UNLINKED | No external identity mapping | Safe first-time identity linking |

All identifiers, email addresses, phone values, business names and order contents must be synthetic reserved test values. Never use a real customer's address, phone, payment instrument or order.

## 5. Common protocol test matrix

Execute each applicable test against every candidate and preserve sanitized request/response evidence. Record pass, fail, blocked or not applicable; never silently omit a test.

| ID | Test | Expected result |
|---|---|---|
| PROTO-01 | Protected Resource Metadata discovery | Correct resource identifier and authorization server metadata are discoverable over HTTPS |
| PROTO-02 | Authorization Server Metadata | Issuer and endpoints are internally consistent; issuer is exact-match validated |
| PROTO-03 | Authorization Code + PKCE S256 | Valid flow succeeds; plain/missing PKCE is rejected |
| PROTO-04 | Redirect URI mismatch | Authorization request is rejected |
| PROTO-05 | State/CSRF validation | Missing, mismatched or replayed state is rejected |
| PROTO-06 | Authorization code replay | Second exchange of the same code is rejected |
| PROTO-07 | Issuer identification | Wrong/missing issuer is rejected where required by the client flow |
| PROTO-08 | Resource/audience binding | Token for another resource or API is rejected by EatHub MCP |
| PROTO-09 | Token validation | Bad signature, wrong issuer/audience/client, expired, not-yet-valid or malformed token is rejected |
| PROTO-10 | Scope minimization | Only explicitly consented and supported scopes are granted |
| PROTO-11 | Refresh rotation | Rotation works; replay of an old refresh token is rejected or triggers documented safe revocation |
| PROTO-12 | Revocation | Revoked authorization cannot invoke tools after the documented revocation boundary |
| PROTO-13 | Signing-key rotation | New keys are accepted after safe JWKS refresh; retired keys follow documented overlap |
| PROTO-14 | Client registration abuse | Untrusted/open registration is disabled or protected by explicit policy, rate limits and monitoring |
| PROTO-15 | Error handling | Errors reveal no tokens, secrets, PII or cross-tenant details |

Where a protocol feature is not applicable to a platform's documented flow, cite the platform contract and record the reason; do not mark it passed by default.

## 6. Platform-specific end-to-end tests

### ChatGPT custom MCP app

- [ ] Current ChatGPT custom MCP app authorization flow completes using the candidate's documented supported client registration/discovery path.
- [ ] CIMD behavior is tested explicitly; do not substitute generic DCR support for CIMD compatibility.
- [ ] PKCE S256, redirect URI, issuer, resource identifier and audience are captured and validated.
- [ ] Consent is shown for the correct EatHub MCP resource and requested scopes.
- [ ] A read-only synthetic tool call succeeds after authorization.
- [ ] A write-capable synthetic tool call is denied unless explicit permission and a confirmation step are present.
- [ ] Disconnect, consent withdrawal and user/membership disablement prevent further calls according to the defined revocation SLA.
- [ ] Reconnect requires the expected fresh authorization and does not restore removed EatHub permissions.

### Claude Remote MCP / Connector

- [ ] Current Claude Remote MCP/Connector connection completes using the documented authorization/bearer-token handoff.
- [ ] Token acquisition and refresh ownership are documented; do not assume the same lifecycle as ChatGPT.
- [ ] Issuer, audience/resource, client and scopes are validated by the MCP authorization boundary.
- [ ] A read-only synthetic tool call succeeds after authorization.
- [ ] Write-capable actions require the same server-side permission and confirmation policy as ChatGPT.
- [ ] Disconnect, token expiry, refresh failure, consent withdrawal and EatHub membership removal are tested.
- [ ] Reconnect cannot restore permissions removed from the EatHub account or membership.

Record ChatGPT and Claude results independently. Passing one platform is not evidence that the other is compatible.

## 7. EatHub identity, tenant and authorization tests

The canonical principal remains `accounts.User`; active EatHub Membership and domain authorization remain authoritative. Provider scopes are coarse consent grants, not tenant authorization.

| ID | Scenario | Expected result |
|---|---|---|
| ID-01 | Existing user completes verified identity link | One issuer-scoped external subject maps to one existing EatHub user |
| ID-02 | Same email, different external subject | No automatic account linking |
| ID-03 | Email changes at provider | Existing mapping remains keyed by issuer + subject |
| ID-04 | Same subject presented by a different issuer | Treated as a different external identity |
| ID-05 | Duplicate external mapping | Link fails closed and is audited |
| TEN-01 | Owner A requests Business A data | Allowed only for currently active membership and role |
| TEN-02 | Owner A requests Business B data | Denied; no data leakage |
| TEN-03 | Multi-business user omits business selection | Denied when explicit selection is required |
| TEN-04 | Multi-business user selects unauthorized business | Denied regardless of client/model-provided context |
| TEN-05 | Staff invokes owner-only operation | Denied by live domain permission check |
| TEN-06 | Customer requests another customer's order | Denied by ownership check |
| REV-01 | User disabled after token issuance | Next tool invocation denied |
| REV-02 | Membership revoked after token issuance | Next tool invocation denied |
| REV-03 | Role downgraded after token issuance | Newly forbidden action denied |
| REV-04 | Consent withdrawn | Tool access denied according to the documented revocation contract |
| FAIL-01 | Identity provider unavailable | Ordinary EatHub login, browsing and ordering remain operational; MCP fails closed |

For every denial, assert both the expected HTTP/protocol outcome and the absence of sensitive data in the response. Validate audit records without storing raw tokens or unnecessary prompt content.

## 8. Iran-facing network and legal evidence

For managed candidates, provider eligibility is a hard gate and must be established in writing before live tests. For self-hosted candidates, document software licensing, lawful hosting, update distribution, dependency provenance, operator responsibility and payment constraints.

After approval, measure the complete authentication dependency chain from consenting testers on representative Iranian mobile and fixed networks, plus a non-Iran control network:

1. DNS resolution and consistency.
2. TCP connection and TLS handshake/certificate validation.
3. Protected Resource Metadata and authorization-server metadata.
4. Authorization redirect and login page.
5. Authentication and consent completion.
6. Authorization-code exchange.
7. JWKS retrieval and key refresh.
8. MCP request with access token.
9. Refresh-token operation, if applicable.
10. Revocation and subsequent denial.

For each stage record UTC timestamp, network type/operator at a non-identifying level, test region, endpoint hostname, DNS/TLS/HTTP outcome, latency, timeout, retry count and sanitized error class. Do not collect subscriber identifiers, exact home addresses, personal IP histories or unrelated traffic. Do not use covert tunnels, location spoofing or provider-policy workarounds.

A single successful homepage request is not a reachability pass. Define a sample size, observation window, latency/error thresholds and repeat schedule before testing. Report median and p95 latency, success ratio, timeout ratio and failure distribution per stage. If legal eligibility is unknown or denied, stop managed-provider testing and record the candidate as unqualified.

## 9. Operational resilience tests

| ID | Failure injection | Expected behavior |
|---|---|---|
| OPS-01 | Provider authorization endpoint unavailable | MCP authorization fails closed; normal EatHub operations continue |
| OPS-02 | JWKS endpoint temporarily unavailable | Valid cached keys follow a documented bounded policy; unknown keys fail closed |
| OPS-03 | Signing key rotates | No unbounded trust or acceptance of invalid signatures |
| OPS-04 | Provider latency increases | Bounded timeout/retry; no request pile-up or cascading outage |
| OPS-05 | Provider account/tenant suspended | Alert and documented incident path; no silent fallback to weaker auth |
| OPS-06 | Identity mapping store unavailable | No fallback to email/phone linking; tool action denied |
| OPS-07 | Audit sink unavailable | Sensitive/write actions follow an explicit fail-safe policy; no silent unlogged mutation |

Document RTO/RPO expectations, support SLA, incident escalation, backup/restore, upgrade cadence, key ownership, exportability and provider exit steps for each deployment mode.

## 10. Evidence ledger and scoring

Create one evidence row per test and per candidate. Required columns:

- Candidate and deployment mode
- Test ID and platform
- Result: Pass / Fail / Blocked / N/A
- Date/time and test environment
- Software/provider version and relevant configuration identifiers (never secret values)
- Sanitized evidence reference
- Expected vs actual behavior
- Severity and impact
- Owner and reviewer
- Remediation and retest reference

Use the ADR-ARCH-06D weights without changing them during the bake-off:

| Category | Weight |
|---|---:|
| ChatGPT MCP OAuth compatibility | 15 |
| Claude Remote MCP compatibility | 15 |
| Existing EatHub identity continuity | 15 |
| Tenant and permission security | 15 |
| Iran legal eligibility and reachability | 20 |
| Reliability and operational control | 8 |
| Cost and commercial feasibility | 5 |
| Operational complexity and lock-in | 7 |
| **Total** | **100** |

Score 0–5 only when supported by evidence. Mark missing evidence Unverified. Any hard-gate failure overrides the numeric score and disqualifies the candidate until a reviewed remediation passes. Do not average away a security or legal failure.

## 11. Stop conditions

Stop the affected candidate's test immediately if any of the following occurs:

- Provider eligibility, lawful payment, licensing or user-country permission is denied or unclear.
- Test unexpectedly reaches production data or a real user account.
- A token, secret, personal data or sensitive prompt is exposed in logs, traces or artifacts.
- Cross-tenant data is returned or an unauthorized action succeeds.
- Resource/audience/issuer validation can be bypassed.
- Revoked or disabled users retain tool access beyond the approved revocation boundary.
- The test requires location/identity misrepresentation or circumvention of provider/network restrictions.
- Provider terms or data residency differ materially from the approved scope.

Preserve only sanitized incident evidence, revoke test credentials where appropriate, notify the security/privacy owner and record the incident before resuming.

## 12. Exit criteria and decision handoff

The PoC may be considered complete only when:

1. All pre-flight approvals are documented.
2. Both ChatGPT and Claude flows pass independently for the selected candidate.
3. All protocol, identity, tenant, negative and revocation tests pass or have formally accepted, bounded exceptions.
4. Iran-facing eligibility and network evidence are complete for managed candidates; self-hosted licensing and operations evidence is complete for self-hosted candidates.
5. Reliability, cost, support, data residency and exit evidence are reviewed.
6. The evidence ledger and weighted scorecard are independently reviewed by engineering, security/privacy and product owners.
7. A separate decision ADR records the selected architecture, rejected alternatives, residual risks and explicit approvals.

Only after the decision ADR is approved may implementation planning begin. This runbook does not authorize production provider accounts, secrets, OAuth runtime, schema changes, migration, DNS, deployment, AI data processing or changes to `main`/ `production`.
