# Business API Tenant Context Migration Audit

Status: initial route inventory, based on `feat/tenant-context-resolver` at commit `8787125405d81cd176894f6fabd0ee7d1543305e`.

## Contract

- A business-scoped request must resolve an explicit business context from `X-Business-Id`.
- The header is a selector, never proof of access. The server validates the authenticated user's active membership and the business status.
- Missing context returns `400 BUSINESS_CONTEXT_REQUIRED`; an unknown, inactive, or unauthorized membership returns `403 BUSINESS_ACCESS_DENIED`.
- A request must never silently select the first membership.
- `Membership.is_active` represents membership eligibility, not the user's globally selected business.

## Current route inventory

| Area | Routes / views | Current base | Migration status |
|---|---|---|---|
| Account business profile | `BusinessProfileAPIView` | `TenantAPIView` | Legacy compatibility |
| Account inventory settings | `BusinessInventorySettingsAPIView` | `ExplicitTenantAPIView` | Explicit context |
| Core dashboard | `DashboardAPIView` | `ExplicitTenantAPIView` | Explicit context (PR #52) |
| Inventory stock balances | `StockBalanceListAPIView` | `ExplicitTenantAPIView` | Explicit context (PR #52) |
| Inventory master data | Items, warehouses | `TenantAPIView` | Pending |
| Inventory compound materials | List/create/detail | `TenantAPIView` | Pending |
| Inventory operations | Issues, transfers, stocktakes, opening stock, movements | `TenantAPIView` | Pending |
| Inventory recipes | Recipes, inputs, outputs | `TenantAPIView` | Pending |
| Inventory reservations | List/create/detail/availability | `TenantAPIView` | Pending |
| Product / Sales | Menus, menu items, orders, refunds, customers, customer accounts and transactions | `TenantAPIView` | Pending |
| Upload | `UploadAPIView` | `APIView` | User-scoped; not business-scoped by current implementation |
| Public menu | `PublicRestaurantMenuAPIView` | `APIView` + `AllowAny` | Public route; no authenticated tenant header |

The Customer and Financial functionality currently exposed through `products/views.py` is included in the Product / Sales route group above; separate `customer/views.py` and `financial/views.py` contain no view implementations in this revision.

## Safe incremental rollout

1. Keep legacy endpoints working for users with exactly one eligible business during migration.
2. Reject ambiguous legacy context when more than one eligible business exists; never use `.first()` or another implicit ordering to choose a tenant.
3. Migrate one route group at a time to `ExplicitTenantAPIView`, updating frontend header propagation and endpoint tests in the same PR.
4. Verify cross-business isolation, missing-header behavior, unauthorized business IDs, inactive memberships, and business deactivation for every migrated group.
5. Remove the legacy base only after the route inventory has no remaining consumers.

## Immediate migration order

1. Core dashboard and stock-balance endpoints (explicit context migrated in PR #52); continue with Inventory master data and operations.
2. Product / Sales endpoints, including Customer and CustomerAccount operations.
3. Account business profile.
4. Remove `TenantAPIView` and its compatibility behavior.

## Guardrails

- Do not enable a global Django tenant middleware: DRF authentication populates `request.user` after Django middleware.
- Do not treat `SelectBusinessAPIView` as server-side tenant authorization; client-side selection is tab-local.
- Every migrated business-scoped frontend request must send `X-Business-Id`; query-cache keys must include business ID and stale in-flight requests must not leak across business switches.
- Do not merge a route migration until PostgreSQL CI and the relevant cross-tenant tests pass.
