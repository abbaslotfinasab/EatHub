export const orderQueryKeys = {
    all: ["orders"] as const,
    business: (userId: number | null, businessId: number | null) =>
        ["orders", userId, businessId] as const,
    list: (userId: number | null, businessId: number | null, filters: unknown) =>
        ["orders", userId, businessId, "list", filters] as const,
    detail: (userId: number | null, businessId: number | null, orderId?: string) =>
        ["orders", userId, businessId, "detail", orderId] as const,
    consumption: (userId: number | null, businessId: number | null, orderId?: string) =>
        ["orders", userId, businessId, "consumption", orderId] as const,
    refund: (userId: number | null, businessId: number | null, orderId?: string) =>
        ["orders", userId, businessId, "refund", orderId] as const,
};
