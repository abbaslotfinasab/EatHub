# Menu API: PATCH contract

Endpoint: `PATCH /api/products/menus/{menu_id}/update/`

The `items` property has replacement semantics when it is present in the
request body:

- **Omitted `items`**: leave the menu's existing items unchanged. This is
  suitable for updating menu metadata or other fields without touching items.
- **Non-empty `items` array**: the array is the complete desired item set.
  Existing items included by their `id` are updated; entries without an `id`
  create new items. Existing items omitted from the array are deleted.
- **Empty `items: []`**: explicitly remove all items from the menu.

For example, sending one existing item in `items` does not mean "update only
that item"; it means that item is the entire resulting collection. Clients
that edit one item in the collection should therefore either send the full
desired collection or use the dedicated item endpoints:

- `PATCH /api/products/menu-items/{item_id}/update/` to update one item.
- `DELETE /api/products/menu-items/{item_id}/delete/` to remove one item.

The endpoint is business-scoped. Item IDs must belong to the menu being
updated; duplicate IDs are rejected. New items require both `name` and
`price`.

This contract is covered by
`MenuItemRecipeApiTests.test_menu_patch_items_array_is_the_complete_replacement_set`.
