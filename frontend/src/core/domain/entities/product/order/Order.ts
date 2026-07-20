// core/domain/entities/sales/Order.ts


export const OrderStatus = {

    PENDING: "pending",

    CONFIRMED: "confirmed",

    PREPARING: "preparing",

    READY: "ready",

    COMPLETED: "completed",

    CANCELLED: "cancelled",

} as const;


export type OrderStatusType =
    typeof OrderStatus[keyof typeof OrderStatus];



export const PaymentStatus = {

    PENDING: "pending",

    UNPAID: "unpaid",

    PAID: "paid",

    FAILED: "failed",

    REFUNDED: "refunded",

} as const;


export type PaymentStatusType =
    typeof PaymentStatus[keyof typeof PaymentStatus];



export const PaymentMethod = {

    CASH: "cash",

    CARD: "card",

    CUSTOMER_ACCOUNT: "customer_account",

} as const;


export type PaymentMethodType =
    typeof PaymentMethod[keyof typeof PaymentMethod];



export interface Order {


    id: string;


    customerId?: number;


    customerName?: string;


    customerPhone?: string;


    tableId?: number | null;


    orderType:
        | "dine_in"
        | "takeaway"
        | "delivery";


    status: OrderStatusType;


    paymentStatus: PaymentStatusType;


    paymentMethod: PaymentMethodType;


    subtotal: number;


    discount: number;


    tax: number;


    totalAmount: number;


    notes?: string | null;


    createdAt?: string;


    updatedAt?: string;

}