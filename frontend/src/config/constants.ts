import type {Order} from "../core/domain/entities/product/order/Order.ts";

export const  API_BASE_URL = import.meta.env.VITE_API_BASE_URL

export const NAVBAR_HEIGHT = 64;
export const DRAWER_WIDTH = 320;
export const SIDEBAR_WIDTH = 280;


export const SIDEBAR_COLLAPSED_WIDTH = 80;


export const ORDER_TYPE_CONFIG = {
    dine_in: {
        label: "سالن",
    },
    takeaway: {
        label: "بیرون‌بر",
    },
    delivery: {
        label: "ارسال",
    },
} satisfies Record<
    Order["orderType"],
    {
        label: string;
    }
>;
