import type {OrderStatusType, PaymentMethodType} from "../../entities/product/order/Order.ts";

export type OrderStatusFilter =
    | "ALL"
    | OrderStatusType;


export type OrderOrdering =
    | "-created_at"
    | "created_at"
    | "-total_amount"
    | "total_amount";

export interface OrderFilters {

    search?: string;

    status?: OrderStatusType;

    orderType?:
        | "dine_in"
        | "takeaway"
        | "delivery";

    paymentStatus?:
        | "pending"
        | "unpaid"
        | "paid"
        | "failed"
        | "refunded";

    paymentMethod?: PaymentMethodType;


    fromDate?: string;

    toDate?: string;


    minTotal?: number;

    maxTotal?: number;


    ordering?: OrderOrdering;


}