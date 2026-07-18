
import {
    OrderStatus,
    type OrderStatusType,
} from "../../../domain/entities/product/order/Order";

interface OrderStatusChipProps {
    status: OrderStatusType;
    size?: "small" | "medium";
}

const STATUS_CONFIG = {
    [OrderStatus.PENDING]: {
        label: "در انتظار",
        color: "warning",
    },
    [OrderStatus.CONFIRMED]: {
        label: "تأیید شده",
        color: "info",
    },
    [OrderStatus.PREPARING]: {
        label: "در حال آماده‌سازی",
        color: "info",
    },
    [OrderStatus.READY]: {
        label: "آماده تحویل",
        color: "success",
    },
    [OrderStatus.COMPLETED]: {
        label: "تحویل شده",
        color: "default",
    },
    [OrderStatus.CANCELLED]: {
        label: "لغو شده",
        color: "error",
    },
} satisfies Record<
    OrderStatusType,
    {
        label: string;
        color:
            | "default"
            | "warning"
            | "info"
            | "success"
            | "error";
    }
>;

import { Chip } from "@mui/material";

export const OrderStatusChip = ({
    status,
    size = "small",
}: OrderStatusChipProps) => {
    const config = STATUS_CONFIG[status];

    return (
        <Chip
            label={config.label}
            color={config.color}
            size={size}
            variant="filled"
            sx={{
                minWidth: 110,
                borderRadius: 2,
                fontWeight: 700,
            }}
        />
    );
};