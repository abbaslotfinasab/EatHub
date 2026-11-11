# EatHub Target Architecture Baseline

Status: Approved target architecture; implementation is incremental.
Last reconciled: 2026-11-11
Scope: Backend and frontend evolution.

## 1. Architecture style

EatHub remains a Modular Monolith. Microservices and distributed transactions are explicitly deferred. PostgreSQL remains the shared database with one database alias.

Each module owns its domain rules, application use cases, persistence, and public contracts. Cross-module calls use application-level ports/use cases and DTOs. Direct imports of another module's ORM models, repositories, or Unit of Work are prohibited in the target architecture. Temporary legacy exceptions must be isolated and removed through small migration PRs.

## 2. Module ownership

- **Accounts / Identity:** Users, businesses, memberships, authentication and authorization context.
- **Customer / CRM:** Business-scoped customer master data and customer lifecycle.
- **Product Catalog:** Reusable product identity, SKU, categories, media references, product lifecycle and manual product declarations (including allergens/dietary tags).
- **Sales:** Menus, MenuItems, menu-specific descriptions and prices, orders, order snapshots, fulfillment and customer-facing reservation lifecycle.
- **Inventory:** Ingredients, ingredient lots, ingredient allergen declarations, recipes, computed recipe allergen profiles, production batches, finished-product lots, stock ledger, reservations, consumption, returns quarantine and recall execution.
- **Purchase:** Suppliers, purchasing and receipt workflows.
- **Financial:** Wallet/account ledger, payments, refunds and financial adjustments.
- **Storage:** File/blob lifecycle; business modules store references rather than storage implementation details.

## 3. Tenant context and authorization

A user may have multiple active Business memberships. Every business-scoped request selects exactly one Business context. The client selector (currently `X-Business-Id`) is not authorization: the server validates that the business is active and the authenticated user has an active membership and the required permission.

Missing context fails closed with HTTP 400 `BUSINESS_CONTEXT_REQUIRED`. Invalid, inactive or unauthorized membership fails with HTTP 403 `BUSINESS_ACCESS_DENIED`. Implicit first-membership fallback is prohibited.

Frontend selected-business state is tab-scoped. Business-scoped API requests send the selected ID; query-cache keys include the business ID; switching business cancels or discards stale requests and isolates cached data. Do not enable global tenant middleware before authentication ordering and cross-tenant tests prove it safe.

## 4. Product, MenuItem and Recipe boundaries

- Product Catalog owns reusable Product identity and lifecycle: `DRAFT`, `ACTIVE`, `ARCHIVED`.
- Sales owns Menu and MenuItem presentation, menu-specific price and availability. MenuItem is not Product.
- One Catalog Product may be reused by multiple MenuItems. MenuItem price is authoritative for the sale.
- Inventory owns Recipe definitions and computed Recipe allergen profiles. Recipe allergen profiles are derived from direct and compound ingredients at read time; they are not persisted as duplicate state.
- A Sales MenuItem may reference a Recipe. Sales validates and reads that reference through the Inventory application boundary; it must not import Inventory ORM models or repositories.
- Catalog Product allergen declarations and Recipe-derived allergen profiles are independent sources. MenuItem read models expose them separately as `catalog_product_allergens` and `recipe_allergens`. Do not silently aggregate one into the other or write one source back to the other.
- Allergen presence `contains` is stronger than `may_contain`. An empty declaration list means no declarations are registered; it is not proof that a product is allergen-free. Dietary suitability must not be inferred merely from absence of allergens.
- OrderItem stores immutable sale-time snapshots. Later Catalog or MenuItem changes must not rewrite historical orders.

## 5. Restrictions, recall and traceability

Product restrictions are separate from Product lifecycle. A business-level Product declaration or restriction is not itself a regulatory certification. Inventory owns operational recall execution and lot/batch disposition; Sales consumes public sellability contracts rather than inspecting Inventory tables.

Target traceability chain:
`IngredientLot → ProductionBatch → FinishedProductLot → Inventory Allocation/Consumption → OrderItem → Customer/Fulfillment`.

Stock-tracked products require finished-product lot traceability. `NON_STOCK` products are exempt from physical lot tracking. Inventory allocation uses FEFO for dated lots and FIFO when expiry is absent; quarantined, recalled or expired lots are ineligible for ordinary allocation.

## 6. Reservation and stock movement

Reservation and Consumption are separate operations. The target flow reserves stock when an order is accepted and records actual consumption at the fulfillment handoff point. Cancellation or eligible payment expiry releases reservations. Confirmed orders must not have reservations silently auto-expired. Partial fulfillment records consumed and remaining quantities separately.

All stock operations must be idempotent, auditable and retain lot references. Returns enter quarantine first; returned goods become sellable only after quality assessment. Financial owns monetary refunds; Inventory owns physical stock disposition; Sales owns order and fulfillment lifecycle.

## 7. Transactions and asynchronous work

Cross-module use cases may share an outer application transaction only when they demonstrably use the same database connection and a verified lock protocol. PostgreSQL concurrency tests are required for row-lock semantics; SQLite is not sufficient evidence.

Use a Transactional Outbox for durable event publication and idempotent asynchronous processing. Never hold a database transaction open while waiting for an external payment/network provider. If databases are separated in the future, use Saga/compensation rather than assuming distributed ACID.

## 8. Migration strategy

Use Expand–Migrate–Contract:
1. Add new contracts/adapters alongside legacy behavior.
2. Migrate callers and data incrementally while preserving API compatibility.
3. Verify data, permissions, tenant isolation and behavior with tests.
4. Remove legacy paths only after all consumers have migrated.

Each implementation slice should be a small PR into `develop`, include focused tests, pass all CI checks on its current head, and have a compatibility/rollback plan. Long-lived branches are limited to `develop`, `main` and `production`; feature branches are short-lived. Production deployment requires explicit approval.

## 9. Deferred contracts

Define these at the implementation slice that needs them; do not block unrelated development with speculative design:
- Exact Sales ↔ Inventory reservation/consumption API, lock ordering and idempotency keys.
- Sales/Purchase ↔ Financial payment, settlement and refund contracts.
- Detailed permission matrix and endpoint-level tenant policy.
- Recall notification and customer-contact workflow.
- Production yield, partial-output and lot genealogy details.

## 10. Implementation status and next sequence

Already integrated into `develop`:
- Multi-membership and explicit tab-scoped business context.
- Product Catalog backend/frontend foundation and MenuItem-to-Catalog Product linking.
- OrderItem Catalog Product identity snapshot.
- Product allergen/dietary declarations and database enum constraints.
- Ingredient allergen declarations and computed Recipe allergen profiles.
- Sales Recipe validation/read integration through the Inventory application boundary, with separate Recipe and Catalog allergen outputs.

Next implementation focus:
1. Complete the Sales order lifecycle audit and identify remaining direct cross-module dependencies.
2. Define and implement the Sales ↔ Inventory reservation/consumption contract in a focused vertical slice, including PostgreSQL concurrency and idempotency tests.
3. Verify order state transitions, cancellation, partial fulfillment and reservation release.
4. Continue Purchase/Financial integration only where a concrete use case requires it.
5. Keep architecture boundary checks and tenant-isolation regression tests in CI.

This document describes the target and current integration points; it does not claim that every target workflow above is already implemented.
