import {
    Divider,
    Stack,
    Typography,
} from "@mui/material";

import ReceiptRoundedIcon from "@mui/icons-material/ReceiptRounded";
import type {Order} from "../../../../domain/entities/product/order/Order";
import {formatCurrency} from "../../../utils/formatCurrency";


interface ReceiptSummaryProps {
    order: Order;
}

export function ReceiptSummary({
                                   order,
                               }: ReceiptSummaryProps) {

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

                <ReceiptRoundedIcon
                    color="primary"
                />

                <Typography
                    variant="h6"
                    sx={{
                        fontWeight: 700,
                    }}
                >
                    خلاصه مالی
                </Typography>

            </Stack>

            <Divider/>

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
                        جمع سفارش
                    </Typography>

                    <Typography
                        sx={{
                            fontWeight: 600,
                        }}
                    >
                        {formatCurrency(order.subtotal)}
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
                        تخفیف
                    </Typography>

                    <Typography
                        sx={{
                            color: "success.main",
                            fontWeight: 600,
                        }}
                    >
                        {order.discount > 0
                            ? `-${formatCurrency(order.discount ?? 0)}`
                            : formatCurrency(0)}
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
                        مالیات
                    </Typography>

                    <Typography
                        sx={{
                            fontWeight: 600,
                        }}
                    >
                        {formatCurrency(order.tax ?? 0)}
                    </Typography>

                </Stack>


                <Divider
                    sx={{
                        my: 1,
                    }}
                />


                <Stack
                    sx={{
                        flexDirection: "row",
                        justifyContent: "space-between",
                        alignItems: "center",
                    }}
                >

                    <Typography
                        variant="h5"
                        sx={{
                            fontWeight: 800,
                        }}
                    >
                        مبلغ قابل پرداخت
                    </Typography>


                    <Typography
                        variant="h4"
                        sx={{
                            color: "primary.main",
                            fontWeight: 800,
                        }}
                    >
                        {formatCurrency(order.totalAmount)}
                    </Typography>

                </Stack>


            </Stack>

        </Stack>

    );

}