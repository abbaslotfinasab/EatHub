export type CustomerBalanceFilter =
    | "ALL"
    | "CREDITOR"
    | "DEBTOR"
    | "ZERO";


export type CustomerMinOrdersFilter =
    | "ALL"
    | "5"
    | "10"
    | "50";


export type CustomerOrdering =
    | "-created_at"
    | "created_at"
    | "-total_spent"
    | "-total_orders"
    | "name";


export interface CustomerSearchFilters {

    search?: string;

    balance?: CustomerBalanceFilter;

    minOrders?: CustomerMinOrdersFilter;

    ordering?: CustomerOrdering;

    createdAfter?: string;

    createdBefore?: string;

}