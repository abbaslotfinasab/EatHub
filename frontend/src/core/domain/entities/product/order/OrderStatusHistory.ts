import type {OrderStatusType} from "./Order.ts";

export interface OrderStatusHistoryEntry {
    id: number;
    fromStatus: OrderStatusType | null;
    toStatus: OrderStatusType;
    actor: {
        id: number;
        name: string;
    } | null;
    createdAt: string;
}

export interface OrderStatusHistory {
    orderId: string;
    history: OrderStatusHistoryEntry[];
}
