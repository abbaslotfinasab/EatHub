export interface DashboardOrder {
    id: string;
    tableNumber: number;
    customerName?: string;

    itemsCount: number;

    totalPrice: number;

    status:
        | "pending"
        | "preparing"
        | "ready"
        | "completed"
        | "cancelled";

    createdAt: string;
}