import type {OrderStatusType} from "../../../domain/entities/product/order/Order.ts";

export interface OrderStatusHistoryEntryDTO {
    id: number;
    from_status: OrderStatusType | null;
    to_status: OrderStatusType;
    actor: {
        id: number;
        name: string;
    } | null;
    created_at: string;
}

export interface OrderStatusHistoryDTO {
    order_id: number | string;
    history: OrderStatusHistoryEntryDTO[];
}
