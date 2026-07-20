import type {
    OrderStatusType,
    PaymentStatusType,
    PaymentMethodType,
} from "./Order";


export interface UpdateOrderStatusInput {


    orderId: string;


    status: OrderStatusType;


    paymentStatus: PaymentStatusType;


    paymentMethod: PaymentMethodType;

}