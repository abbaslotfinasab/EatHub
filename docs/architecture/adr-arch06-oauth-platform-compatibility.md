# ADR-ARCH-06B — OAuth and Platform Compatibility for EatHub MCP

- **Status:** Proposed; provider selection and identity architecture require explicit review
- **Date:** 2026-11-25
- **Baseline:** `develop` after PR #253 (merge commit `6b4bbe82ea0b194625217fd735dc98f88978a679`)
- **Scope:** Authentication and authorization compatibility for the ChatGPT MCP app/plugin surface and Claude Remote MCP integrations
- **Non-goals:** Selecting a paid identity provider, implementing OAuth endpoints, changing account flows, adding migrations, or deploying an MCP server

## 1. Why this ADR exists

ADR-ARCH-06 (PR #253) proposed an EatHub-owned OAuth 2.1 authorization-server boundary backed by the existing EatHub account system. A follow-up review of current first-party platform documentation shows that the protocol requirements are more specific than a generic Authorization Code + PKCE flow.

The purpose of this ADR is to record those requirements and prevent implementation against an incomplete or outdated OAuth assumption. This document is a compatibility assessment, not approval to build or buy an identity system.

## 2. Verified platform requirements

### 2.1 ChatGPT custom MCP app/plugin surface

The current OpenAI developer documentation describes a custom remote MCP server that can be connected in ChatGPT as a plugin. The server can expose tools and optional UI; the UI is not required for a tools-only first release.

For an authenticated MCP server, the documented contract includes:

- OAuth 2.1 authorization-code flow with PKCE using `S256`.
- Protected Resource Metadata (RFC 9728) served by the MCP resource server, normally at `/.well-known/oauth-protected-resource`, or advertised through a `WWW-Authenticate` challenge.
- Authorization-server discovery metadata.
- The `resource` parameter echoed through authorization and token requests and represented in the resulting token audience/resource claim.
- Client identification/registration through Client ID Metadata Documents (CIMD), Dynamic Client Registration (DCR), or predefined clients, according to the selected setup.
- Token endpoint authentication methods advertised accurately. Current docs describe CIMD public-client exchange using `none` and signed client assertions using `private_key_jwt`.
- Issuer identification (RFC 9207) for the stable redirect flow: metadata advertises `authorization_response_iss_parameter_supported=true`, and successful and error authorization responses include an exact matching `iss`.
- The MCP resource server validates token signature, issuer, audience/resource, expiry/not-before, scopes and EatHub's live domain permissions on every request.
- Unauthenticated/invalid requests return a standards-compatible `401` challenge pointing to protected-resource metadata. Tool metadata must declare security schemes consistently.

OpenAI recommends using an established identity provider rather than implementing authentication from scratch. This recommendation is important: PR #253's initial preference for a custom EatHub authorization server must remain a proposal until a provider-vs-custom implementation assessment is complete.

OpenAI documentation also describes an OpenAI-managed client certificate for transport-level identification of the ChatGPT MCP client. This is supplemental client identification only; it does not replace end-user OAuth authentication or EatHub authorization.

### 2.2 Claude Remote MCP

The current Anthropic MCP Connector documentation describes connecting to a remote MCP server from the Messages API without implementing a separate MCP client.

The documented connector contract includes:

- A remotely reachable HTTPS MCP server.
- Streamable HTTP or SSE transport.
- MCP tool calls through the Messages API.
- An optional OAuth bearer token supplied as `authorization_token` in the MCP server configuration.
- The API integrator is responsible for obtaining and refreshing the OAuth token before making API requests.
- The connector feature currently documents tool invocation support; do not assume MCP resources, prompts, elicitation, or a complete interactive UI are supported by this API connector.

This means Claude's API connector and ChatGPT's hosted app surface are not identical OAuth clients. The same EatHub resource server and authorization policy can serve both, but token acquisition, refresh, connection lifecycle and user experience may be owned by different platform/client layers.

This assessment is specifically about Anthropic's Messages API MCP Connector. Claude Desktop/other Claude surfaces must be validated separately before claiming identical behavior.

## 3. Compatibility matrix

| Capability | ChatGPT custom MCP app/plugin | Claude Messages API MCP Connector | EatHub implication |
|---|---|---|---|
| Remote MCP over HTTPS | Yes | Yes | One public, stable MCP endpoint |
| Streamable HTTP | Supported | Supported | Preferred transport candidate; verify SDK and hosting behavior |
| SSE | Supported | Supported | Keep compatibility tests if enabled |
| OAuth bearer token | OAuth flow managed by ChatGPT | Token supplied by API caller | Shared resource-server token validation |
| OAuth discovery | Protected Resource Metadata + AS metadata | Client-side token acquisition is caller responsibility | Publish standards-compliant metadata |
| Authorization Code + PKCE | Required for documented OAuth flow; S256 | Depends on token acquisition client; use standard flow | Authorization server must support secure public clients |
| Resource/audience binding | `resource` echoed and token audience validated | Resource server validates audience | Tokens must be audience-restricted to EatHub MCP |
| Client registration | CIMD, DCR, or predefined client | Depends on API caller's OAuth client | Do not couple EatHub user identity to platform client identity |
| User consent | ChatGPT authorization UI | Managed by the integrating application/client | EatHub consent and scopes must be explicit and auditable |
| Refresh lifecycle | ChatGPT handles normal token expiry/rotation with server support | Caller obtains/refreshes token | Provider/client integration needs a tested refresh strategy |
| Tool-level auth metadata | Security schemes and auth challenge behavior | Tool allow/deny configuration and bearer token | Tool registry owns platform-neutral policy; adapters map metadata |
| Transport client identity | OpenAI-managed mTLS certificate may be available | No equivalent assumption made here | Treat transport identity as defense-in-depth, never user identity |

## 4. Architecture consequences

1. Keep the MCP resource server and application capability contracts platform-neutral.
2. Keep ChatGPT and Claude adapters responsible for their own connection and consent UX.
3. Resolve the EatHub principal from a validated bearer token. Never trust a platform user ID, email, model argument or client-supplied tenant ID as the actor.
4. Treat OAuth scopes as consent boundaries only. Re-check current EatHub business membership, customer ownership, role and domain permission for each tool invocation.
5. Use a resource-specific audience and issuer validation. A valid token for another API is not valid for EatHub MCP.
6. Keep external platform client identity separate from the EatHub principal and from per-business customer relationships.
7. Anonymous public discovery may be exposed without OAuth only when the DTO is intentionally public and contains no private customer/operator data. All customer-specific and write tools require authenticated context.
8. No platform-specific approval UI replaces EatHub's exact confirmation, idempotency or domain validation for consequential writes.

## 5. Identity-provider decision: options to evaluate

### Option A — Established identity provider / authorization server

Evaluate an existing provider that can issue tokens for the EatHub MCP resource and satisfy current ChatGPT MCP requirements (CIMD and/or DCR, PKCE S256, metadata discovery, resource parameter handling, issuer identification, token endpoint methods and refresh/revocation).

Required integration shape:

- Existing EatHub account remains the canonical business principal, or is securely federated to the provider identity.
- A stable issuer/subject mapping resolves to exactly one EatHub principal.
- Account linking requires an authenticated EatHub session or equivalent strong verification; never auto-link solely by matching email or phone.
- Provider-issued tokens are accepted only after complete issuer/audience/signature/lifetime/scope validation.
- EatHub still performs live business/customer ownership and permission checks.

Advantages: avoids writing a security-critical OAuth server and aligns with OpenAI's recommendation.

Risks/questions: account migration or federation complexity, provider availability and cost, regional/data processing constraints, subject stability, refresh-token custody, account recovery, and whether all required metadata behaviors are supported without custom work.

### Option B — Custom EatHub authorization server

Build and operate OAuth authorization endpoints integrated with the existing Django account system.

Advantages: direct control over EatHub login, account recovery, principal mapping and policy.

Risks: EatHub assumes responsibility for OAuth protocol correctness, metadata, PKCE, CIMD/DCR, resource indicators, issuer mix-up defenses, key rotation/JWKS, refresh-token rotation/revocation, consent, abuse detection, security updates and ongoing operations. This is not equivalent to adding a JWT endpoint to the existing DRF setup.

This option must not be selected merely because the current account system already uses JWT. The existing SimpleJWT access/refresh flow is not, by itself, the MCP OAuth authorization-server contract.

### Option C — Hybrid federation

Use an established OAuth authorization server while federating authentication to the existing EatHub account system, with a stable issuer/subject-to-EatHub-principal mapping and EatHub-owned resource authorization.

This is the preferred option to evaluate first, not an approved vendor or final decision. It may preserve the current account source of truth while avoiding a home-grown OAuth protocol implementation, provided account recovery, linking, logout/revocation and tenant authorization remain correct.

## 6. Required provider bake-off

Before selecting an option, run a time-boxed technical spike against at least one established provider and a custom-server feasibility prototype only if needed.

The provider must demonstrate, with captured test evidence:

- Protected Resource Metadata discovery and correct authorization-server discovery.
- Exact `resource` propagation from authorization request to token request and resulting audience claim.
- PKCE S256.
- CIMD support for the ChatGPT client mode, or DCR if selected; supported token endpoint authentication methods.
- RFC 9207 `iss` behavior on both successful and error authorization responses if using the stable ChatGPT redirect mode.
- JWKS publication, key rotation behavior, signature validation and issuer stability.
- Short-lived access tokens, refresh rotation, revocation and logout behavior.
- Secure account linking to an existing EatHub principal without email/phone auto-link.
- Same test principal can authenticate from ChatGPT and the Claude integration path without creating duplicate EatHub users.
- Invalid issuer, wrong audience, expired/revoked token, missing scope and cross-business requests are rejected.
- Provider outage does not disable ordinary EatHub web/mobile authentication or ordering.
- Data residency, DPA, subprocessors, cost, support and operational ownership are reviewed before procurement.

## 7. Security invariants

- Token validation is mandatory on every protected MCP request.
- No client credentials grant, service-account identity or model-supplied actor is accepted as a substitute for end-user authorization for customer/operator tools.
- Never accept a tenant/business/customer selector as authorization proof.
- The MCP server is a resource server, not a generic proxy to internal APIs.
- No direct ORM/database access from the MCP adapter.
- Customer and operator authorization remain separate.
- Every write capability requires domain validation, permission, audit and idempotency; consequential actions additionally require explicit confirmation bound to the exact operation.
- Platform outage, OAuth provider outage or AI kill switch must not impair ordinary EatHub operations.

## 8. Open decisions

1. Approve a managed-provider/hybrid bake-off as the default next investigation, rather than immediately implementing a custom OAuth server.
2. Confirm whether the existing EatHub account remains the canonical login and how a provider federates to it.
3. Choose the exact ChatGPT surface for first release: custom MCP app/plugin with optional UI, or another supported app surface. Do not conflate the custom MCP plugin surface with the Responses API's server-to-server MCP tool integration.
4. Confirm whether Claude's first release is the Messages API MCP Connector, Claude Desktop remote MCP, or both.
5. Decide the minimum anonymous discovery tools and customer-authenticated tools for the first release.
6. Approve data residency, provider DPA and retention requirements before sending customer data to any AI platform.

## 9. Sources reviewed

- OpenAI, Authentication for MCP plugins: https://developers.openai.com/plugins/build/auth
- OpenAI, Build an MCP server: https://developers.openai.com/plugins/build/mcp-server
- OpenAI, Add custom MCP server: https://developers.openai.com/api/docs/guides/custom-mcp-server
- Anthropic, MCP Connector: https://platform.claude.com/docs/en/agents-and-tools/mcp-connector

Platform behavior can change. Re-run this compatibility checklist against the exact target product and account/workspace configuration immediately before implementation and release.

## 10. Approval boundary

This ADR is a proposal. It changes no runtime behavior, authentication configuration, API, database schema, migration, provider account, secret, or deployment. A separate implementation ADR/PR must follow an explicit identity-provider decision and security review.
