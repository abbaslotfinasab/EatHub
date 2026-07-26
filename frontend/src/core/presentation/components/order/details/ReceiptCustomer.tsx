import {
    Divider,
    Stack,
    Typography,
} from "@mui/material";

import PersonRoundedIcon from "@mui/icons-material/PersonRounded";
import type {Order} from "../../../../domain/entities/product/order/Order.ts";


interface ReceiptCustomerProps {
    order: Order;
}

export function ReceiptCustomer({
    order,
}: ReceiptCustomerProps) {

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

            <PersonRoundedIcon
                color="primary"
            />

            <Typography
                variant="h6"
                sx={{
                    fontWeight: 700,
                }}
            >
                اطلاعات مشتری
            </Typography>

        </Stack>

        <Divider />

        <Stack
            sx={{
                gap: 1.5,
            }}
        >

            <Stack
                sx={{
                    flexDirection: "row",
                    justifyContent: "space-between",
                }}
            >

                <Typography
                    sx={{
                        color: "text.secondary",
                    }}
                >
                    نام مشتری
                </Typography>

                <Typography
                    sx={{
                        fontWeight: 600,
                    }}
                >
                    {order.customerName || "-"}
                </Typography>

            </Stack>

            <Stack
                sx={{
                    flexDirection: "row",
                    justifyContent: "space-between",
                }}
            >

                <Typography
                    sx={{
                        color: "text.secondary",
                    }}
                >
                    شماره تماس
                </Typography>

                <Typography>
                    {order.customerPhone || "-"}
                </Typography>

            </Stack>

            {order.orderType === "dine_in" && (

                <Stack
                    sx={{
                        flexDirection: "row",
                        justifyContent: "space-between",
                    }}
                >

                    <Typography
                        sx={{
                            color: "text.secondary",
                        }}
                    >
                        شماره میز
                    </Typography>

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
                }}
            >

                <Typography
                    sx={{
                        color: "text.secondary",
                    }}
                >
                    نوع سفارش
                </Typography>

                <Typography
                    sx={{
                        fontWeight: 600,
                    }}
                >
                    {order.orderType === "dine_in"
                        ? "حضوری"
                        : order.orderType === "delivery"
                            ? "ارسال"
                            : "بیرون‌بر"}
                </Typography>

            </Stack>

        </Stack>

    </Stack>

);

}