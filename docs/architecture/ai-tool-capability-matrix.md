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


## 11. Customer ordering and order tracking — deeper As-Is audit

Audit source: current `develop` after merge commit `ed7f5446e0d59313205c05584dfa9bfcd50d3a3a`. Findings below describe existing code, not approved AI exposure.

### 11.1 Customer identity and ownership

- The `Customer` model has an optional nullable FK to the authenticated EatHub `User` model. This is a potential identity-link primitive only; it is not sufficient proof of a customer account/ownership workflow.
- The inspected `CustomerService.create_customer` creates or reuses a customer by `(business, phone)` and updates the name. It does not bind `Customer.user` to an authenticated user.
- Customer list/detail/create/update/delete endpoints use `ExplicitTenantAPIView` and `IsAuthenticated`; no customer-self-scoped endpoint was found in the inspected customer and products routes.
- Customer read DTOs include name, phone, balance, total orders, total spent and creation date. Detail additionally includes account and transaction history. These are restaurant CRM views, not customer self-service contracts.
- Therefore a ChatGPT customer identity must not be inferred from a phone number, prompt, order payload or model-supplied customer ID. Identity linking, verified ownership and account recovery must be designed explicitly.

### 11.2 Existing order creation

- `POST /api/products/orders/` is `OrderCreateAPIView(ExplicitTenantAPIView)`, requires an authenticated principal and `ORDERS_CREATE`, and resolves the business from the authenticated membership plus `X-Business-Id`.
- Input includes a UUID idempotency key, optional `customer_id`, order type, menu item IDs, quantities, and optional notes/table.
- The service checks that a supplied customer belongs to the resolved business; menu items are loaded with a business filter. This prevents cross-business customer/menu-item references at the service boundary.
- Idempotency is scoped to `(business, idempotency_key)` with a canonical payload fingerprint. Reusing the same key with a different payload is rejected; concurrent duplicate creation is recovered by checking the existing row after the unique-constraint conflict.
- The endpoint returns the broad `OrderSerializer`, including customer, business, payment method/status, subtotal, discount, tax, total, customer balance, notes, and item details. This response must not be reused as an AI customer response.
- The current create service query filters menu items by business but does not itself filter out items with `is_available=False` or require the parent menu's `is_active=True`. This is a release-blocking validation gap for public/AI ordering unless enforced by another verified layer; none was found in the inspected create path.

### 11.3 Public discovery and menu correctness

- `GET /api/products/{slug}/menu/` is anonymous and rejects inactive businesses.
- `DjangoMenuReadRepository.list_public_for_business` filters only by business ID and orders menus; it does not filter `Menu.is_active` and does not pre-filter related `MenuItem.is_available`.
- `PublicMenuSerializer` and `PublicRestaurantSerializer` both declare `fields = "__all__"`. The item serializer is allowlisted, but the menu and business envelopes are not.
- Existing public-menu tests verify active-business rejection and payload shape, but do not verify exclusion of inactive menus or unavailable items.
- Before an AI menu-search tool is enabled, public query semantics must be corrected and regression-tested: active business, active/published menus, available items only, explicit allowlisted fields, verified allergens, price/currency semantics and availability freshness.

### 11.4 Order reads and lifecycle

- Restaurant order list/detail are authenticated tenant endpoints requiring `ORDERS_VIEW`; repository reads filter by `business_id`. Tests cover missing business context, unauthorized membership, permission denial, and tenant-scoped list/detail repository behavior.
- The list endpoint accepts operator filters including customer name/phone search, status, order type, payment state/method, date and amount. This is an operator query, not a customer-owned order-history query.
- The order serializer exposes PII and financial fields, so a new minimal operator DTO and a separate customer DTO are required.
- Status changes require operation-specific permissions: `ORDERS_UPDATE`; cancellation additionally requires `ORDERS_CANCEL`; selected inventory-sensitive transitions require `INVENTORY_ORDER_FULFILL`; payment fields require a financial role and `PAYMENTS_MANAGE`.
- Status history is append-only and tenant-scoped. Payment events are append-only and restricted to financial access. These are useful audit foundations but do not create customer authorization or customer tracking endpoints.
- No customer-facing status subscription, notification contract, or order lookup by verified customer identity was found in the inspected routes.

### 11.5 Recommended customer flow for EatHub ChatGPT app and Claude

1. **Discover:** anonymous `restaurant.search` and `restaurant.get_public_menu` over strictly public, filtered DTOs.
2. **Build cart:** platform conversation state holds a draft cart; server revalidates restaurant, menu item availability, price and quantity at every checkout attempt. Do not trust model-held prices or totals.
3. **Authenticate/link:** user signs in through an explicit OAuth authorization flow; server maps provider subject to an EatHub principal. Customer ownership is verified and linked to the selected business only through a deliberate account-linking process.
4. **Prepare order:** server creates a short-lived order quote/draft with authoritative item snapshots, calculated totals, taxes/fees and expiry. The quote is bound to the authenticated principal, business, and a version/fingerprint.
5. **Confirm:** ChatGPT/Claude presents the exact restaurant, items, quantities, fulfilment type, address/table details and final amount. No order write occurs before explicit user confirmation.
6. **Place:** a dedicated customer-order application use case validates quote expiry, current availability/prices, actor ownership and business policy; it uses idempotency bound to actor + business + checkout attempt. It must not call the operator-only `OrderCreateAPIView` with a fabricated operator context.
7. **Track:** return a minimal customer-owned tracking DTO; every read checks order ownership against the authenticated EatHub principal and tenant. Do not accept a raw order ID as authorization.
8. **Cancel/support:** only expose permitted transitions with explicit confirmation and policy checks; refunds/payment changes remain a separate, later financial capability.

### 11.6 Customer-order capability disposition

| Proposed tool | Actor | Required authorization | Side effect | Current readiness |
|---|---|---|---|---|
| `restaurant.search` | Anonymous customer | Public visibility policy | Read | Blocked on discovery implementation and public DTO policy |
| `restaurant.get_public_menu` | Anonymous customer | Active business + active menu/item policy | Read | Blocked on query filtering and serializer allowlist |
| `cart.prepare` | Anonymous or authenticated customer | Server-validated public catalog; cart bound to session/principal | Draft only | Not implemented; safe to design |
| `checkout.quote` | Authenticated customer | OAuth identity + verified customer/business relationship | Quote creation only | Not implemented |
| `order.place` | Authenticated customer | Customer-order permission, confirmed quote, fresh validation, idempotency | Write | Not available; requires dedicated use case |
| `order.track` | Authenticated customer | Verified ownership + tenant scope | Read | Not available; no self-scoped route |
| `order.cancel` | Authenticated customer | Ownership + cancellable-state policy + confirmation | Write | Not available as customer capability |
| Operator `orders.list` / `orders.get` | Restaurant operator | `ORDERS_VIEW` and active business membership | Read | Existing API; do not expose current broad serializer |

### 11.7 Required tests before customer ordering exposure

- Unauthenticated and unlinked user cannot quote, place, or track an order.
- A linked customer cannot read or mutate another customer's order, even within the same business.
- A customer cannot cross business boundaries by changing business, menu, menu-item, customer, quote or order IDs.
- Inactive business, inactive menu, unavailable item, changed price and expired quote are rejected at checkout.
- Replaying the same idempotency key and same payload returns the same order; replay with changed payload is rejected; concurrent requests do not create duplicate orders.
- Client/model-supplied prices, totals, discounts, payment states, customer IDs and tenant IDs are ignored or rejected.
- Confirmation is bound to the exact quote version and final total; any material change requires a new confirmation.
- Customer response DTO excludes other customer data, operator notes, internal cost, wallet balance, payment event metadata and unrelated business details.
- Operator permissions remain independent; the customer path must not inherit `ORDERS_CREATE` or `ORDERS_VIEW` merely because it uses the same order aggregate.

### 11.8 Audit conclusion

Current code provides useful restaurant-operator order creation, tenant-scoped operator reads, business-scoped menu-item lookup, UUID idempotency and append-only order/payment audit. It does **not** yet provide a verified customer identity-linking journey, customer-owned order history/tracking, customer checkout quote, customer cancellation contract, or public-menu correctness guarantees. The ChatGPT app and Claude connector must wait for these dedicated customer capabilities rather than exposing operator APIs.
