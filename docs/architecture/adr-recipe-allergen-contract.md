# ADR: Recipe Allergen Profiles Across Inventory, Sales, and Catalog

- Status: Accepted for implementation planning
- Date: 2026-11-10
- Scope: Inventory Recipe allergen derivation, Sales MenuItem read models, and Catalog Product declarations
- Parent architecture: Modular Monolith; PostgreSQL; explicit business context

## Context

Inventory owns Ingredients, compound materials, Recipes, and ingredient allergen declarations. Catalog owns reusable Products and their business-entered allergen and dietary declarations. Sales owns MenuItems and associates each MenuItem with an optional Catalog Product and an optional Recipe.

A Catalog Product may be linked to multiple MenuItems, and each MenuItem may use a different Recipe. Therefore a single Product-level allergen profile cannot safely be inferred by copying or aggregating one MenuItem's Recipe profile. Doing so would make the Product declaration dependent on menu-specific preparation and could silently overwrite business-entered declarations.

The current Django implementation still has the legacy `products` app owning Menu and MenuItem persistence and serializers. Some presentation code imports Inventory's Recipe ORM model directly. This is an existing boundary violation to remove as the Sales extraction proceeds; it is not a precedent for the new contract.

## Decisions

### 1. Inventory is the source of truth for recipe-derived allergen profiles

Inventory owns the computation and semantics of a Recipe allergen profile.

- The profile is derived at read time from the Recipe's ingredient inputs.
- Direct raw ingredients contribute their declared allergens.
- Semi-prepared ingredients contribute the allergen declarations of their raw compound components, according to the existing Inventory recipe derivation rules.
- For the same allergen code, `contains` takes precedence over `may_contain`.
- The profile is not persisted as a duplicate of ingredient declarations. Ingredient declaration changes must be reflected in subsequent profile reads.
- The query must be business-scoped and must not disclose a Recipe or Ingredient belonging to another business.

Inventory exposes this capability through an application-level query/use case and immutable DTOs. The DTO contains the Recipe identity, business identity, and a stable ordered collection of allergen code/presence pairs. Consumers must not import Inventory ORM models or Django repositories.

Dietary suitability tags are not inferred from allergens or Recipe ingredients in this contract. In particular, vegan, vegetarian, halal, kosher, and gluten-free are not safely derivable from allergen absence alone.

### 2. Sales consumes the Inventory contract through an application port

Sales owns the MenuItem-facing use case and response shape. It may depend on an application-level port that describes the required Recipe allergen profile query, but Sales application/domain code must not depend on Inventory ORM models or infrastructure repositories.

The modular-monolith composition layer wires the Sales port to Inventory's public application query. The adapter must pass the validated business context and Recipe ID explicitly.

A missing Recipe produces an explicit absent profile, not an inferred empty-safe profile. A Recipe that belongs to another business is rejected using the established tenant access semantics.

### 3. MenuItem responses keep recipe and catalog declarations separate

For a MenuItem linked to both a Recipe and a Catalog Product, the Sales read model exposes two distinct sources:

- `recipe_allergens`: the computed Inventory profile for this MenuItem's Recipe.
- `catalog_product_allergens`: the manually declared Catalog Product allergen profile, obtained through a Catalog application contract.

The API must not merge these sources into one unqualified list and must not write recipe-derived values back to Catalog Product.

A Product reused by multiple MenuItems retains one Catalog declaration, while each MenuItem exposes its own Recipe-derived profile. A MenuItem without a Recipe has no recipe-derived profile; it must not be represented as allergen-free.

### 4. Reconciliation is explicit and non-destructive

Sales (or a dedicated read-model/application service) may provide a comparison between the two profiles, but it must preserve provenance and never mutate either source.

For each allergen code:
- A recipe `contains` value conflicting with a catalog declaration of absence is a conflict.
- A recipe `may_contain` value conflicting with a catalog declaration of absence is also a conflict; the weaker presence still cannot be silently discarded.
- If both sources declare the allergen, the stronger presence can be shown while retaining both source values.
- If only one source declares an allergen, report it as source-only/incomplete reconciliation, not as proof that the other source is wrong.
- Missing Catalog declarations and missing Recipe profiles are distinct from an explicit empty declaration.

The comparison is informational. It does not certify legal compliance, guarantee cross-contact absence, or replace operator review and applicable food-label requirements.

### 5. Business isolation and dependency direction remain mandatory

- Every query is scoped by an explicitly validated business ID.
- Business IDs are selectors, never authorization.
- Cross-module communication uses application ports, use cases, and DTOs only.
- Direct cross-module ORM/repository imports are prohibited.
- No implicit first-membership or default-business fallback is permitted.

## Implementation sequence

1. Complete and review the Inventory ingredient/Recipe allergen capability.
2. Add a Catalog application query that returns the manually declared Product allergen profile for a Product within a business.
3. Define the Sales application port and MenuItem read DTO without importing Inventory or Catalog ORM models.
4. Wire adapters at the composition boundary and expose separate source fields in the MenuItem API.
5. Add reconciliation as a pure application/domain policy with exhaustive tests for contains/may_contain, source-only, missing-source, and conflicting declarations.
6. Remove the legacy direct Inventory Recipe ORM import from Products/Sales presentation code as part of the Sales boundary migration.

## Non-goals

- No Product-level automatic allergen aggregation across its MenuItems.
- No automatic mutation of Catalog Product declarations from Recipe data.
- No inference of dietary suitability tags from allergen declarations.
- No persisted duplicate Recipe allergen profile.
- No microservice split or cross-service messaging for this read path.
- No claim of allergen-free safety or legal certification.

## Acceptance criteria

- Inventory remains the sole owner of Recipe-derived allergen semantics.
- Catalog remains the sole owner of manually entered Product declarations.
- Sales exposes both sources with explicit provenance and does not conflate them.
- A reusable Product linked to multiple MenuItems can expose different Recipe profiles without data loss or cross-contamination.
- Missing, empty, and conflicting profiles are distinguishable.
- Tenant isolation is enforced at every application boundary.
- Tests cover raw ingredients, compound ingredients, precedence, multi-MenuItem reuse, missing profiles, and conflicting declarations.
- No cross-module ORM or repository dependency is introduced.
