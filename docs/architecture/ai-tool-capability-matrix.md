# ARCH-06 — AI Tool Capability Matrix (As-Is Baseline)

> Status: architecture audit artifact; no AI/MCP runtime or API/schema change is introduced by this document.
> Baseline: `develop` at `fbf33256473270fb3ad69f00c4f7918d02c6abcf`.
> Scope: shared EatHub AI core, ChatGPT app/plugin-style integration, and Claude integration.

## 1. Product and platform decision

EatHub will expose one platform-neutral application capability layer to multiple clients:

- **ChatGPT:** ship an installable/discoverable EatHub ChatGPT app (the product may be called a plugin in user-facing language). Implement the current ChatGPT Apps SDK / MCP integration surface rather than coupling the backend to a retired or provider-specific legacy plugin contract.
- **Claude:** expose the same capabilities through a Claude-compatible remote MCP integration.
- **Shared core:** authenticated identity mapping, server-resolved business context, authorization, tool registry, typed input/output DTOs, policy enforcement, audit, idempotency and application use cases.
- **Provider-specific edge:** ChatGPT UI/metadata and Claude connector/auth configuration remain adapters. Neither adapter owns business rules.
- **Domain source of truth:** existing EatHub application/domain use cases and repositories. AI/MCP must not access Django ORM or database tables directly.

The ChatGPT app and Claude connector are two clients of the same server-side capability contracts; neither gets a privileged or broader data model by default.

## 2. Current-state findings

### Authentication and tenant context

- DRF defaults to JWT authentication; SimpleJWT access lifetime is 15 minutes and refresh lifetime is 7 days (rotation and blacklist enabled in the inspected settings).
- No OAuth authorization-server / external provider OAuth flow was found in the inspected settings or account routes. This is an audit finding, not proof that no isolated OAuth code exists anywhere.
- `ExplicitTenantAPIView` resolves `X-Business-Id` against the authenticated user's active membership on the server and attaches business, membership, role and permissions to the request.
- `TenantAPIView` retains a single-business compatibility fallback; multi-business users must provide a valid explicit business header.
- **Security rule:** an AI model, tool argument, prompt, ChatGPT client, or Claude client must never select or assert an authoritative `business_id`, role, permission, or actor. The server derives these from the authenticated principal and active membership. Client-provided business selection may only be treated as an untrusted selection request and must be revalidated.

### Capability observations

- Public restaurant menu: `PublicRestaurantMenuAPIView` allows anonymous access and resolves only active businesses by slug. Its current serializers use `fields = "__all__"` for Business and Menu; this is too broad for AI exposure and must be replaced with explicit public DTOs/allowlists before release.
- Tenant menu reads: `MenuListAPIView` and `MenuDetailAPIView` use `ExplicitTenantAPIView` and `DjangoMenuReadRepository` scoped by business ID. The views instantiate repositories directly, so they are not yet the desired application boundary for AI reuse.
- Catalog reads: list/detail require `PRODUCTS_VIEW`, pass the server-resolved business ID to `list_products` / `get_product`, and use application use cases and repository ports. This is the strongest currently observed candidate for an initial authenticated read-only tool.
- Inventory balances: require `INVENTORY_VIEW` and pass server-resolved business ID to `ListStockBalancesUseCase`; however, the view constructs Django repositories directly. The response includes quantity and average cost, so average cost is sensitive business data and should be excluded from customer-facing tools.
- Inventory item and warehouse reads: require `INVENTORY_VIEW` and pass business ID to tenant-scoped repository methods. These are restaurant-operator capabilities, not public/customer capabilities.
- Order list/detail: require `ORDERS_VIEW` and use tenant-scoped order repository methods. The current `OrderSerializer` includes customer data, business details, payment fields, totals, notes and customer balance. It is not a safe AI DTO. There is no evidence in the inspected routes of customer-self-scoped order history; do not expose these endpoints as customer tools.
- Business profile: authenticated tenant context exists, but the serializer is broad and the view uses a compatibility tenant base class. Do not expose wholesale to AI until a purpose-built allowlisted DTO and application query boundary exist.
- Customer account, payment events, refunds, financial adjustments, inventory mutations and order state changes are sensitive/write capabilities. They remain out of initial exposure.

## 3. Initial capability matrix

| Capability | Intended actor | Current permission / scope evidence | Data sensitivity | Side effect | Idempotency evidence | AI disposition |
|---|---|---|---|---|---|---|
| Discover active restaurant by slug | Anonymous customer | Public endpoint; active-business lookup | Public only after DTO allowlist | None | N/A | Candidate after serializer hardening |
| Read public restaurant menu | Anonymous customer | Public endpoint; menu query scoped to resolved business | Public menu fields only; current serializer is over-broad | None | N/A | Candidate after explicit public DTO and tests |
| Search/list catalog products | Restaurant operator | `PRODUCTS_VIEW`; server-resolved business ID; application use case | Internal catalog data | None | N/A | First authenticated read-only candidate |
| Get catalog product | Restaurant operator | `PRODUCTS_VIEW`; business-scoped use case | Internal catalog data | None | N/A | First authenticated read-only candidate |
| Read private menus | Restaurant operator | `IsAuthenticated` + `ExplicitTenantAPIView`; repository scoped by business | Internal menu/pricing/recipe references | None | N/A | Hold: add explicit permission and application query boundary |
| Read inventory items / warehouses | Restaurant operator | `INVENTORY_VIEW`; business-scoped repository methods | Internal operational data | None | N/A | Candidate after use-case/port boundary and DTO review |
| Read stock balances | Restaurant operator | `INVENTORY_VIEW`; use case receives business ID | High: quantities and average cost | None | N/A | Hold: split safe stock availability from cost data; adapter cleanup |
| Read restaurant orders | Authorized restaurant operator | `ORDERS_VIEW`; business-scoped repository | High: customer PII, order notes, payment state and totals | None | N/A | Hold: minimal order DTO, explicit field policy and audit |
| Read customer order history | Customer | No customer-self-scoped route verified | High: personal/order data | None | N/A | Not available until ownership model and tests are verified |
| Create/modify menu or catalog | Restaurant operator | Existing write permissions vary by endpoint | Internal business data | Yes | Not consistently established | Later phase; confirmation + idempotency required |
| Create/update/cancel order | Customer or restaurant operator | Existing permissions differ by operation | Customer, operational and financial | Yes | Create has UUID idempotency key; other operations require review | Later phase; explicit confirmation and actor-specific policy |
| Refund / payment / account balance | Financially authorized operator | Financial role and permission checks exist on some paths | Critical financial data | Yes | Refund has idempotency key; full workflow review required | Excluded until dedicated security review |
| Inventory mutation / stocktake / transfer | Restaurant operator | Operation-specific permissions must be audited | High operational/financial impact | Yes | Per-operation review required | Excluded from first release |
| Admin / cross-tenant operations | Authorized platform admin only | No AI-specific authorization contract exists | Critical | Often yes | N/A | Excluded; no cross-tenant AI tools |

## 4. Initial tool contract candidates

These are proposed capabilities, not claims that production-ready MCP tools already exist.

### Public/customer discovery
1. `restaurant.search` — search only active/public restaurants; return a strict public restaurant card.
2. `restaurant.get_public_menu` — input a public slug; return only published/active menu and item fields. Never return internal IDs or fields unless required by the public contract.
3. `menu.search_items` — search across public menu data with availability and allergen information only where verified and maintained.

### Authenticated restaurant operator
4. `catalog.list_products` — pagination and bounded search; require server-authenticated operator and `PRODUCTS_VIEW`.
5. `catalog.get_product` — tenant-scoped product detail; return an allowlisted DTO.
6. `inventory.list_items` / `inventory.list_warehouses` — require `INVENTORY_VIEW`; do not include cost or supplier-sensitive fields.
7. `inventory.get_stock_availability` — separate availability/quantity from average cost; restrict to an explicitly authorized operator tool.

### Explicitly not in first exposure
- Customer order history, order detail, customer records, customer balances, payments, refunds, financial events, supplier/purchase data, inventory writes, menu writes, order writes, staff/user administration and cross-tenant admin operations.

## 5. Mandatory contract for every tool

Every registered tool must declare and validate:

- Stable tool name, version, description and owning domain.
- Supported actor classes (anonymous customer, authenticated customer, restaurant operator, platform operator) and explicit exclusions.
- Authentication method and identity mapping; no model-supplied actor identity.
- Required permission(s), resolved server-side.
- Tenant/business resolution policy; no trusted tenant ID from tool arguments.
- Strict input schema, bounded pagination/search, validation and safe defaults.
- Explicit output DTO with field-level data classification and redaction.
- Side-effect classification (read / write / financial / sensitive).
- Idempotency strategy for writes and duplicate/replay behavior.
- Confirmation policy for all writes; stronger confirmation for financial or irreversible operations.
- Audit fields: actor, tenant, platform/client, tool/version, request/trace ID, authorization decision, outcome, latency and cost. Avoid logging secrets or unnecessary PII.
- Error mapping that does not reveal whether another tenant's resource exists.
- Positive and negative tests, especially unauthorized actor, missing permission, cross-tenant ID substitution, inactive membership, malformed input, replay and data-redaction cases.

## 6. Platform-neutral execution flow

1. ChatGPT app or Claude client invokes the provider adapter / MCP endpoint.
2. Server authenticates the connection and maps it to an EatHub principal.
3. Server resolves active membership and business context; tool arguments cannot override them.
4. Tool registry validates schema, actor, permission and data policy.
5. Application capability invokes the appropriate use case / query service.
6. Domain/application layer accesses persistence through ports and adapters.
7. Response is mapped to a minimal versioned DTO and redacted.
8. Audit/trace metadata is recorded; response returns through the platform adapter.

No AI provider receives database credentials, ORM access, unrestricted API tokens or secrets. Provider prompts and context must be minimized; tenant isolation and authorization are enforced before model-visible output is constructed.

## 7. Architecture work required before implementation

1. Add a dedicated AI application layer and typed capability contracts; do not place provider logic in domain modules.
2. Add identity linking and OAuth/authorization design for ChatGPT app installation and Claude connector authentication. Keep the current JWT login flow intact for first-party clients.
3. Create explicit public menu DTOs; remove `fields = "__all__"` from any serializer used by an AI/public tool.
4. Add application query/use-case boundaries for menu and inventory read capabilities; remove direct repository construction from AI-facing presentation paths.
5. Define customer identity and ownership rules before any customer order-history capability.
6. Split operational stock visibility from cost visibility.
7. Build tool-level authorization, redaction, idempotency, confirmation and audit middleware/policies.
8. Add contract tests shared by ChatGPT and Claude adapters; provider adapters must not fork domain behavior.
9. Add kill switch, provider timeout, bounded retries, rate limits, tenant/user budgets and graceful degradation. AI outages must not affect normal EatHub operations.

## 8. Release sequence

- **Phase A — As-Is audit:** continue endpoint, serializer, permission, use-case and test evidence collection.
- **Phase B — Contracts and threat model:** finalize actors, OAuth/identity, tenant policy, data classification, DTOs and ADRs.
- **Phase C — Shared core:** identity/context, gateway, provider adapters, registry, audit and policy enforcement.
- **Phase D — Read-only MCP tools:** public discovery first, then authenticated catalog/inventory tools after evidence and tests.
- **Phase E — Platform integrations:** ChatGPT Apps SDK app and Claude remote MCP connector using the same tool contracts.
- **Phase F — Controlled writes and hardening:** only after explicit permission, confirmation, idempotency, audit and negative tests are proven.

## 9. Open audit questions

- Confirm exact permission and queryset scoping for every customer, order, inventory and purchase endpoint.
- Inspect serializers for all candidate read paths and classify every returned field.
- Verify whether current public menus filter inactive menus/items and whether public allergen data is authoritative.
- Verify tenant isolation for all related IDs accepted by write serializers (for example customer, menu item, recipe, warehouse and ingredient IDs).
- Determine supported OAuth authorization flow and current ChatGPT Apps SDK / Claude MCP requirements during Phase B; do not hard-code assumptions from legacy plugin specifications.
- Verify audit coverage and idempotency semantics for every write operation before exposure.

## 10. Non-goals of this baseline

- No AI/MCP code, database schema, migration, OAuth provider, API route or production configuration is introduced here.
- No change to `main` or `production`.
- No direct ORM or database access from AI tools.
- No write or financial tool is approved by this matrix.
