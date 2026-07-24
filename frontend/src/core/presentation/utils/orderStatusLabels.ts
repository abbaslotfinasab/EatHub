import type {OrderStatusType} from "../../domain/entities/product/order/Order.ts";

export const orderStatusLabels: Record<OrderStatusType, string> = {

    pending: "در انتظار",

    confirmed: "تایید شده",

    preparing: "در حال آماده‌سازی",

    ready: "آماده تحویل",

    completed: "تکمیل شده",

    cancelled: "لغو شده",

};