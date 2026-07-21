export interface MenuFilters {
    isActive?: boolean;
    search?: string;   // جستجو در name, category
}



export type MenuStatusFilter =
    | "ALL"
    | "ACTIVE"
    | "INACTIVE";

export type MenuItemsFilter =
    | "ALL"
    | "HAS_ITEMS"
    | "EMPTY";

export type MenuOrdering =
    | "-created_at"
    | "created_at"
    | "name"
    | "sort_order";
