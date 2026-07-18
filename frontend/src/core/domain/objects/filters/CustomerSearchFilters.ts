export interface CustomerSearchFilters {
    search?: string;

    hasDebt?: boolean;

    ordering?:
        | "name"
        | "-name"
        | "created_at"
        | "-created_at";
}