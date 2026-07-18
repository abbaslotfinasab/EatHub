// presentation/components/order/OrderTypeSelector/orderTypes.ts

import type { SvgIconComponent } from "@mui/icons-material";

import {
    DeliveryDiningRounded,
    LocalDiningRounded,
    TakeoutDiningRounded,
} from "@mui/icons-material";

export type OrderTypeValue =
    | "dine_in"
    | "takeaway"
    | "delivery";

export interface OrderTypeItem {
    value: OrderTypeValue;

    title: string;

    description: string;

    icon: SvgIconComponent;
}

export const ORDER_TYPES: OrderTypeItem[] = [
    {
        value: "dine_in",
        title: "داخل سالن",
        description: "سفارش برای مشتری داخل رستوران",
        icon: LocalDiningRounded,
    },
    {
        value: "takeaway",
        title: "بیرون‌بر",
        description: "تحویل حضوری به مشتری",
        icon: TakeoutDiningRounded,
    },
    {
        value: "delivery",
        title: "ارسال",
        description: "ارسال توسط پیک",
        icon: DeliveryDiningRounded,
    },
];