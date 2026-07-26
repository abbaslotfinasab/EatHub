import {
    Chip,
    Divider,
    Stack,
    Typography,
} from "@mui/material";

import ReceiptLongRoundedIcon from "@mui/icons-material/ReceiptLong";
import AccessTimeRoundedIcon from "@mui/icons-material/AccessTimeRounded";
import RestaurantRoundedIcon from "@mui/icons-material/RestaurantRounded";
import TableRestaurantRoundedIcon from "@mui/icons-material/TableRestaurantRounded";
import PaymentsRoundedIcon from "@mui/icons-material/Payments";
import {formatDateTime} from "../../../utils/formatDateTime.ts";
import {OrderStatusChip} from "../OrderStatusChip.tsx";
import type {Order} from "../../../../domain/entities/product/order/Order.ts";




interface ReceiptOrderInfoProps {
    order: Order;
}

export function ReceiptOrderInfo({
    order,
}: ReceiptOrderInfoProps) {

    const orderTypeLabel =
        order.orderType === "dine_in"
            ? "حضوری"
            : order.orderType === "delivery"
                ? "ارسال"
                : "بیرون بر";

    const paymentStatusLabel =
        order.paymentStatus === "paid"
            ? "پرداخت شده"
            : order.paymentStatus === "pending"
                ? "در انتظار"
                : order.paymentStatus === "unpaid"
                    ? "پرداخت نشده"
                    : order.paymentStatus === "failed"
                        ? "ناموفق"
                        : "برگشت داده شده";

   return (

    <Stack
        sx={{
            gap: 2,
        }}
    >

        <Stack
            sx={{
                flexDirection: "row",
                gap: 1,
                alignItems: "center",
            }}
        >

            <ReceiptLongRoundedIcon color="primary" />

            <Typography
                variant="h6"
                sx={{
                    fontWeight: 700,
                }}
            >
                اطلاعات سفارش
            </Typography>

        </Stack>

        <Divider />

        <Stack
            sx={{
                gap: 2,
            }}
        >

            <Stack
                sx={{
                    flexDirection: "row",
                    justifyContent: "space-between",
                    alignItems: "center",
                }}
            >

                <Stack
                    sx={{
                        flexDirection: "row",
                        gap: 1,
                        alignItems: "center",
                    }}
                >

                    <ReceiptLongRoundedIcon fontSize="small" />

                    <Typography
                        sx={{
                            color: "text.secondary",
                        }}
                    >
                        شماره سفارش
                    </Typography>

                </Stack>

                <Typography
                    sx={{
                        fontWeight: 600,
                    }}
                >
                    #{order.id}
                </Typography>

            </Stack>

            <Stack
                sx={{
                    flexDirection: "row",
                    justifyContent: "space-between",
                    alignItems: "center",
                }}
            >

                <Stack
                    sx={{
                        flexDirection: "row",
                        gap: 1,
                        alignItems: "center",
                    }}
                >

                    <AccessTimeRoundedIcon fontSize="small" />

                    <Typography
                        sx={{
                            color: "text.secondary",
                        }}
                    >
                        زمان ثبت
                    </Typography>

                </Stack>

                <Typography
                    sx={{
                        fontWeight: 600,
                    }}
                >
                    {formatDateTime(order.createdAt)}
                </Typography>

            </Stack>

            <Stack
                sx={{
                    flexDirection: "row",
                    justifyContent: "space-between",
                    alignItems: "center",
                }}
            >

                <Stack
                    sx={{
                        flexDirection: "row",
                        gap: 1,
                        alignItems: "center",
                    }}
                >

                    <RestaurantRoundedIcon fontSize="small" />

                    <Typography
                        sx={{
                            color: "text.secondary",
                        }}
                    >
                        نوع سفارش
                    </Typography>

                </Stack>

                <Chip
                    size="small"
                    label={orderTypeLabel}
                />

            </Stack>

            {order.orderType === "dine_in" && (

                <Stack
                    sx={{
                        flexDirection: "row",
                        justifyContent: "space-between",
                        alignItems: "center",
                    }}
                >

                    <Stack
                        sx={{
                            flexDirection: "row",
                            gap: 1,
                            alignItems: "center",
                        }}
                    >

                        <TableRestaurantRoundedIcon
                            fontSize="small"
                        />

                        <Typography
                            sx={{
                                color: "text.secondary",
                            }}
                        >
                            شماره میز
                        </Typography>

                    </Stack>

                    <Typography
                        sx={{
                            fontWeight: 600,
                        }}
                    >
                        {order.tableId ?? "-"}
                    </Typography>

                </Stack>

            )}

            <Stack
                sx={{
                    flexDirection: "row",
                    justifyContent: "space-between",
                    alignItems: "center",
                }}
            >

                <Typography
                    sx={{
                        color: "text.secondary",
                    }}
                >
                    وضعیت سفارش
                </Typography>

                <OrderStatusChip
                    status={order.status}
                />

            </Stack>

            <Stack
                sx={{
                    flexDirection: "row",
                    justifyContent: "space-between",
                    alignItems: "center",
                }}
            >

                <Stack
                    sx={{
                        flexDirection: "row",
                        gap: 1,
                        alignItems: "center",
                    }}
                >

                    <PaymentsRoundedIcon
                        fontSize="small"
                    />

                    <Typography
                        sx={{
                            color: "text.secondary",
                        }}
                    >
                        وضعیت پرداخت
                    </Typography>

                </Stack>

                <Chip
                    color={
                        order.paymentStatus === "paid"
                            ? "success"
                            : order.paymentStatus === "failed"
                                ? "error"
                                : "warning"
                    }
                    size="small"
                    label={paymentStatusLabel}
                />

            </Stack>

        </Stack>

    </Stack>

);

}