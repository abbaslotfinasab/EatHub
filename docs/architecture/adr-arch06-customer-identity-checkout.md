# ADR-ARCH-06 — Customer Identity, MCP Authorization, and Checkout Contract

- **Status:** Proposed; requires product/security review before runtime implementation
- **Date:** 2026-11-25
- **Target baseline:** `develop` at `ab1227f22c370dbcea9507871e9af91680747f97`
- **Scope:** Shared identity and customer-order contracts for the EatHub ChatGPT app and Claude remote MCP integration
- **Non-goals:** Implementing OAuth endpoints, migrations, checkout APIs, payment processing, or platform deployment

## 1. Context and verified baseline

The current backend uses DRF JWT authentication with SimpleJWT. The inspected account routes provide registration, login, refresh, current-user and business-selection flows. No OAuth authorization-server flow was found in the inspected settings/routes.

The current `Customer` record has an optional relationship to an EatHub user, but the audited customer creation path does not establish a verified authenticated-user link. Existing customer CRUD and order APIs are restaurant-operator capabilities, not customer self-service APIs.

The existing order-create endpoint requires an authenticated operator with `ORDERS_CREATE` and a server-resolved active business membership. It returns a broad operator serializer and must not be repurposed as a customer checkout endpoint.

The customer and platform integrations must therefore be designed as a distinct application boundary, not as a thin wrapper around existing operator endpoints.

## 2. Decision drivers

1. One identity and authorization model for ChatGPT and Claude.
2. EatHub remains the authority for users, customer ownership, business membership, roles and permissions.
3. Provider subject identity must not be confused with an EatHub user ID or a restaurant's CRM customer record.
4. Tenant/business context is derived and validated by the server for every request.
5. No AI tool accesses ORM models, database credentials or unrestricted internal APIs.
6. Checkout totals and availability are server-authoritative and revalidated immediately before order placement.
7. A model-generated request cannot substitute for explicit user confirmation.
8. Provider outage or AI disablement cannot impair normal web/mobile EatHub flows.

## 3. Proposed identity model

Keep three concepts separate:

- **EatHub principal:** the authenticated `User` account. This is the canonical actor for authorization.
- **External platform identity:** a mapping from a trusted issuer and immutable subject to an EatHub principal. The natural uniqueness key is `(issuer, subject)`; email is profile data, not a stable identity key.
- **Business customer relationship:** the verified association between an EatHub principal and a `Customer` record within one business. It is distinct from operator membership and must be explicitly linked/verified.

A user may have multiple external platform identities, but one issuer/subject must resolve to at most one EatHub principal. Linking an external identity to an existing principal requires an authenticated EatHub session or an equivalent strong account-verification ceremony. Never auto-link accounts solely because email or phone strings match.

Customer ownership is business-scoped. A principal's relationship to a customer record in Business A grants no access to a similarly named or numbered record in Business B.

### 3.1 Identity-link lifecycle

1. Authenticate the user through the EatHub-owned authorization flow.
2. Resolve the external platform identity from a validated issuer/subject claim; never accept a model-supplied subject.
3. If no mapping exists, require deliberate account creation or account-link confirmation.
4. Verify the customer relationship using an existing verified channel or an explicit business-approved linking process.
5. Persist the link with audit metadata (actor, business, method, timestamp, outcome); avoid storing raw verification secrets.
6. Support unlink/revocation and account recovery without silently transferring historical orders.

Open product decision: whether customer identity is global across businesses or each business requires a separate verified customer relationship. This ADR recommends a global EatHub principal with separate per-business customer relationships.

## 4. Proposed authorization boundary

### 4.1 Authorization server

**Recommendation:** implement an EatHub-owned OAuth 2.1 authorization server boundary backed by the existing EatHub user/account system. Do not introduce a second user directory or make a provider's identity service the source of truth.

- Use Authorization Code with PKCE for public/native clients.
- Validate exact registered redirect URIs, issuer, audience/resource, expiry, signature, nonce/state where applicable, and PKCE verifier.
- Use short-lived access tokens and rotating/revocable refresh credentials only where the client/platform contract requires them.
- Keep signing keys and client secrets server-side; never put provider secrets in frontend code, prompts or tool arguments.
- Resource/audience restriction must bind tokens to the EatHub MCP/API resource.
- Provide revocation, consent, account unlink and incident response paths.
- Do not treat OAuth scopes as a replacement for live EatHub permission checks.

This is a proposed architecture, not a claim that the current JWT setup already provides OAuth. The exact authorization-server library/deployment and each platform's current OAuth requirements remain implementation-time compatibility decisions.

### 4.2 Request authorization

For every tool invocation:

1. Validate the bearer token and resolve the EatHub principal.
2. Resolve the requested business selection against that principal's active memberships or verified customer relationships.
3. Derive actor, business, role and permission context on the server.
4. Apply the capability's explicit policy and current domain rules.
5. Invoke an application use case through a typed port/DTO.
6. Audit the decision and outcome with correlation identifiers and redacted metadata.

A client may send a business selector as an untrusted routing hint only. It is never proof of membership or customer ownership. Reject ambiguous multi-business context rather than guessing.

### 4.3 Initial scopes (proposal)

Scopes are coarse consent boundaries, not grants that bypass domain authorization:

| Scope | Intended capability | Initial exposure |
|---|---|---|
| `restaurants:read` | Search publicly visible restaurants | Candidate read-only |
| `menus:read` | Read published public menu DTOs | Candidate read-only after public DTO policy |
| `customer:profile` | Read the caller's minimal linked customer profile | Not enabled until identity linking exists |
| `orders:quote` | Create/read a short-lived checkout quote for the caller | Not enabled until quote use case exists |
| `orders:create` | Place an order from a confirmed quote | Not enabled in first read-only release |
| `orders:read` | Track only caller-owned orders | Not enabled until ownership and DTO tests exist |

No operator, finance, inventory-write, refund, payment-management or cross-tenant administrative scope is approved by this ADR.

## 5. Proposed customer checkout contract

The customer checkout flow is a dedicated application capability and must not call `OrderCreateAPIView` with fabricated operator context.

### 5.1 Quote creation

Input is limited to a business selection, item identifiers/quantities, fulfilment choice and the minimum fulfilment details. The server must:

- Resolve the principal and verified customer relationship.
- Resolve the business from server-validated context.
- Re-read active business, active menu, available menu items and current prices.
- Validate quantities, fulfilment rules, delivery zone and required details.
- Calculate discounts, taxes, fees and final amount using domain-owned rules.
- Produce an opaque quote ID, version/fingerprint, expiry, currency and a customer-safe line-item snapshot.
- Bind the quote to principal + business + checkout attempt; never accept client-supplied price, total, discount, tax, customer ID or tenant ID as authoritative.

A quote is not an order and must not reserve stock or imply payment authorization unless a separately approved domain policy explicitly says so.

### 5.2 Exact confirmation

Before placement, the platform must present the exact restaurant, items, quantities, fulfilment details and final amount to the user. Confirmation must be an explicit user action, not an inference from conversational intent or a model-generated tool call.

The confirmation record must bind to the quote ID and version/fingerprint. Any material change to price, availability, quantity, fulfilment details or total invalidates the confirmation and requires a fresh quote and confirmation.

### 5.3 Order placement

A dedicated customer-order application use case must:

- Authenticate the same principal that owns the quote.
- Revalidate quote expiry, business policy, menu availability and price.
- Verify the confirmation is for the exact current quote version.
- Enforce idempotency scoped by principal + business + checkout attempt.
- Reject same-key/different-payload replay and handle concurrent retries safely.
- Create the order through domain/application services, not direct ORM from MCP.
- Return a minimal customer-owned result DTO; do not reuse the broad operator `OrderSerializer`.

Payment collection/authorization is explicitly outside this contract until a separate payment ADR and provider flow are approved.

### 5.4 Order tracking

Tracking requires an authenticated principal and a server-side ownership check on every request. A raw order ID is an identifier, never an authorization credential.

The response DTO should contain only the minimum customer-relevant state (for example order reference, current status, fulfilment summary and customer-visible timestamps). Exclude operator notes, other customer details, internal costs, account balances, payment event metadata and unrelated tenant data.

## 6. Threats and mandatory controls

| Threat | Required control |
|---|---|
| Model spoofs actor, customer or tenant | Ignore/reject model-supplied identity and tenant authority; derive from authenticated context |
| Cross-business ID substitution | Resolve every referenced object inside the authorized business and test negative cases |
| Account takeover during linking | Strong authenticated linking ceremony, verified channel, audit and unlink/recovery |
| Email collision or recycled phone | Never auto-link on email/phone equality alone |
| Stolen/replayed token | Short expiry, audience restriction, secure storage, rotation/revocation and anomaly logging |
| Redirect/code interception | Exact redirect registration, PKCE, state/nonce validation and one-time authorization codes |
| Stale price or availability | Recompute on quote and again before placement; expire quote |
| Confirmation spoof/replay | Bind confirmation to actor + quote version + final amount + attempt |
| Duplicate order under retry/concurrency | Actor/business/attempt idempotency with canonical payload fingerprint |
| PII or financial leakage to model/provider | Minimized DTOs, field allowlists, redaction, no broad serializers |
| Provider outage or abuse | Rate limits, budget/timeouts, circuit breaker and AI kill switch isolated from core ordering |

## 7. Required application ports and contracts

Names below are conceptual; implementation must align with the existing module boundaries and naming conventions.

- `ExternalIdentityRepository`: resolve/create/revoke issuer-subject mappings.
- `CustomerOwnershipRepository`: resolve a verified customer relationship for principal + business.
- `CustomerCheckoutQuoteService`: create, retrieve, expire and validate quotes.
- `CustomerOrderPlacementService`: place from a confirmed quote with idempotency.
- `CustomerOrderTrackingQuery`: return only caller-owned tracking DTOs.
- `AuthorizationContextResolver`: resolve principal and validated business/customer context.
- `AIInvocationAuditPort`: record actor, capability, tenant, decision, correlation ID, latency and outcome with sensitive values redacted.

The AI/MCP adapter may call only registered application capabilities. It must not instantiate Django repositories, import ORM models or query the database directly.

## 8. Required negative and contract tests

- Missing, invalid, expired, wrong-audience and revoked tokens are denied.
- Wrong issuer/subject, duplicate identity mapping and attempted account takeover are denied.
- Matching email/phone without verified linking does not link accounts.
- Unlinked principals cannot quote, place or track.
- A principal cannot access another customer's record/order in the same business.
- A principal cannot cross businesses by changing business, customer, quote, item or order IDs.
- Operator permissions do not implicitly grant customer permissions and vice versa.
- Client/model-supplied actor, customer, tenant, price, tax, discount and total cannot override server values.
- Inactive business/menu, unavailable item, changed price and expired quote are rejected.
- Confirmation for an older quote version or different final amount is rejected.
- Same idempotency key + same payload is safe under retry; same key + changed payload is rejected; concurrent attempts do not create duplicates.
- Customer DTOs contain no operator-only, financial or cross-tenant fields.
- AI kill switch/provider failure leaves normal EatHub authentication and ordering unaffected.

## 9. Rollout sequence

1. Approve identity semantics, customer-linking policy and account-recovery behavior.
2. Select and threat-model the OAuth authorization-server implementation against current ChatGPT and Claude MCP requirements.
3. Implement identity mapping and customer ownership with migrations, audit and negative tests.
4. Implement read-only public discovery/menu DTOs and policy tests.
5. Implement quote-only capability; do not place orders yet.
6. Implement confirmed customer order placement and ownership-scoped tracking behind feature flags.
7. Add ChatGPT and Claude adapters against the same application contract.
8. Run security, tenant-isolation, load, provider-failure and end-to-end tests before staged rollout.

## 10. Open decisions requiring explicit approval

- Is the customer account global across EatHub, with per-business customer relationships (recommended), or business-specific?
- Which verified channel establishes ownership of an existing restaurant CRM customer record?
- Which OAuth authorization-server implementation is supportable by the existing Django deployment and current platform contracts?
- What exact customer-visible fulfilment and delivery-address data is retained, for how long, and under which consent?
- Which business policies govern quote expiry, price changes, stock reservation and order cancellation?
- Is payment handled by an existing EatHub payment flow or a separate provider integration? No payment behavior is approved here.

## 11. Consequences

**Positive:** ChatGPT and Claude share one identity and application contract; operator/customer permissions remain separate; tenant isolation and checkout correctness are explicit; implementation can proceed incrementally.

**Costs:** OAuth authorization, verified customer linking, quote lifecycle, idempotency and customer-safe DTOs require new application work and tests. This is intentional: exposing operator endpoints directly would be faster but unsafe and architecturally incorrect.

**Approval boundary:** This ADR is a proposal only. No production behavior, API contract, database schema or authorization policy is changed until the open decisions are reviewed and a separate implementation PR is approved.
