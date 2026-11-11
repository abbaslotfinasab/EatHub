# ADR: Customer and Financial Module Ownership

- Status: Accepted for implementation planning
- Date: 2026-11-09
- Scope: Customer/CRM, customer accounts, wallet ledger, and Sales order references
- Parent architecture: Modular Monolith; PostgreSQL; explicit business context

## Context

The `customer` Django app currently contains only its app scaffold. Customer CRUD and wallet/account endpoints are registered under `products/urls.py`, implemented in `products/views.py`, and depend on serializers/services under `products/serializers` and `products/services`. The persistence models `Customer`, `CustomerAccount`, and `CustomerTransaction` are in `products/models.py`.

This is an ownership mismatch, not merely a URL organization issue. Moving model classes between Django apps also affects migration state, content types, admin registration, imports, and foreign-key references. It must not be done as a casual file move.

## Decisions

### 1. Customer owns customer identity and CRM

The Customer module owns:
- Business-scoped customer identity and profile (name, phone, optional linked user).
- Customer CRUD, search, detail, and CRM-facing customer summaries.
- Customer-side validation and application use cases.
- The business-scoped customer API contract.

A customer record is a business-specific relationship/profile. The same human may have separate Customer records in different businesses. Do not introduce global phone uniqueness or merge customers across businesses as part of this migration.

### 2. Financial owns accounts and ledger

The Financial module owns:
- Customer account / wallet balance.
- Opening balance and verification state.
- Credit, debit, adjustment, settlement, refund-credit and reconciliation operations.
- Immutable transaction history and financial authorization rules.

Customer may expose a read-only balance/summary through an application-level query/DTO, but it must not import Financial ORM models or repositories directly. Sales must call Financial application use cases for settlement/refund behavior; it must not manipulate wallet rows directly.

### 3. Sales owns orders, not customer identity or wallet ledger

Sales continues to own Order and OrderItem. An order may reference a Customer through a Customer application contract. Cross-module access must use application ports/use cases and DTOs, not direct imports of another module's ORM models/repositories.

Order history must remain auditable if a Customer profile is archived or removed. A Customer deletion must never cascade-delete orders.

### 4. Business isolation remains mandatory

Customer and Financial business-scoped endpoints must use `ExplicitTenantAPIView` (or the approved explicit tenant-context resolver integration), require `X-Business-Id`, and scope every lookup by `request.business`. The header is a selector, never authorization. Missing context returns `400 BUSINESS_CONTEXT_REQUIRED`; invalid or unauthorized context returns `403 BUSINESS_ACCESS_DENIED`.

No implicit first-membership fallback is permitted for these APIs.

## Current risks discovered

1. `Order.customer` currently uses `on_delete=models.CASCADE`. `CustomerService.delete_customer` blocks deletion for wallet history, paid orders, and order-linked transactions, but does not block every existing order. Deleting a customer with an unpaid/unsettled order can therefore cascade-delete the order. This is a data-loss risk and must be fixed before Customer delete is considered safe.
2. `CustomerService.create_customer` uses `get_or_create(business, phone)`, but the inspected `Customer` model has no database uniqueness constraint for `(business, phone)`. Concurrent requests can create duplicates unless the database enforces the invariant. Before adding the constraint, audit and resolve existing duplicates and define the desired phone normalization policy.
3. `CustomerAccount.customer` is currently a OneToOne relation with `on_delete=models.CASCADE`; `CustomerTransaction.account` also cascades. Moving these models requires a deliberate migration plan and retention policy for financial history.
4. Customer detail/list responses currently combine CRM data with order aggregates and wallet/account data. These should become application-level read models/DTOs, not direct cross-module ORM joins after the boundary is established.
5. Customer and wallet API routes currently share the Products URL namespace. Route ownership should move without breaking existing public API paths; preserve compatibility with URL aliases or a staged route migration.

## Migration plan (expand -> migrate -> contract)

### Phase A — Safety and contracts
- Add regression tests proving that deleting a customer with any order cannot delete that order.
- Decide whether customer deletion becomes archive/soft-delete; default preference is archive when any order/history exists.
- Audit duplicate `(business, normalized phone)` records and define normalization before adding a unique constraint.
- Define Customer and Financial application DTOs/use cases and dependency direction.
- Keep existing database tables and API paths unchanged in this phase.

### Phase B — Customer module extraction
- Introduce Customer application/domain/presentation boundaries.
- Move customer CRUD views, serializers, and service behavior behind Customer-owned interfaces.
- Preserve existing database table names and IDs; use explicit Django migration state/database operations rather than dropping/recreating tables.
- Move URL registration to the Customer app while preserving old paths during compatibility.
- Migrate Customer endpoints to explicit business context and add missing-header / foreign-business tests.
- Keep wallet/account/ledger endpoints out of this PR.

### Phase C — Financial module extraction
- Introduce Financial-owned account and ledger use cases.
- Move account/transaction API ownership and wallet operations behind Financial interfaces.
- Replace Sales-to-Financial direct ORM/service coupling with application ports.
- Preserve ledger rows, settlement markers, refund links, opening-balance verification, and idempotency constraints.
- Add PostgreSQL concurrency and reconciliation tests.

### Phase D — Contract
- Remove legacy Products-owned Customer/Financial views, serializers, services, and imports only after all callers are migrated.
- Remove compatibility URL wiring only after frontend and external clients are verified.
- Update architecture and route ownership audits.

## Explicit non-goals

- No microservice split.
- No cross-business/global customer identity merge.
- No immediate table rename or destructive data migration.
- No broad rewrite of Sales order settlement/refund logic in the Customer extraction PR.
- No removal of legacy routes before compatibility is proven.

## Acceptance criteria

- Customer and Financial each have clear ownership and no direct ORM/repository coupling across module boundaries.
- Existing customer, order, wallet, refund, and ledger data remain intact.
- Customer deletion cannot delete order history.
- Duplicate customer phone policy is enforced at the database level after data cleanup.
- Business-scoped APIs require explicit validated tenant context.
- Existing API consumers continue working throughout the migration.
- Tests cover authorization, isolation, deletion retention, idempotency, and PostgreSQL concurrency where relevant.
