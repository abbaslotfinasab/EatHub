import {
    Chip,
    Divider,
    Stack,
    Typography,
} from "@mui/material";

import PaymentsRoundedIcon from "@mui/icons-material/Payments";
import CreditCardRoundedIcon from "@mui/icons-material/CreditCardRounded";
import AccountBalanceWalletRoundedIcon from "@mui/icons-material/AccountBalanceWalletRounded";
import PersonRoundedIcon from "@mui/icons-material/PersonRounded";
import type {Order} from "../../../../domain/entities/product/order/Order.ts";


interface ReceiptPaymentProps {
    order: Order;
}

export function ReceiptPayment({
    order,
}: ReceiptPaymentProps) {

    const paymentMethodLabel =
        order.paymentMethod === "cash"
            ? "نقدی"
            : order.paymentMethod === "card"
                ? "کارت"
                : "حساب مشتری";

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

    const paymentStatusColor =
        order.paymentStatus === "paid"
            ? "success"
            : order.paymentStatus === "failed"
                ? "error"
                : order.paymentStatus === "refunded"
                    ? "warning"
                    : "default";

    const PaymentMethodIcon =
        order.paymentMethod === "cash"
            ? AccountBalanceWalletRoundedIcon
            : order.paymentMethod === "card"
                ? CreditCardRoundedIcon
                : PersonRoundedIcon;

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

            <PaymentsRoundedIcon
                color="primary"
            />

            <Typography
                variant="h6"
                sx={{
                    fontWeight: 700,
                }}
            >
                اطلاعات پرداخت
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

                    <PaymentMethodIcon
                        fontSize="small"
                    />

                    <Typography
                        sx={{
                            color: "text.secondary",
                        }}
                    >
                        روش پرداخت
                    </Typography>

                </Stack>

                <Typography
                    sx={{
                        fontWeight: 600,
                    }}
                >
                    {paymentMethodLabel}
                </Typography>

            </Stack>


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
                    وضعیت پرداخت
                </Typography>

                <Chip
                    size="small"
                    color={paymentStatusColor}
                    label={paymentStatusLabel}
                />

            </Stack>

        </Stack>

    </Stack>

);

}