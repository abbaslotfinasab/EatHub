import {
    Avatar,
    Divider,
    Paper,
    Stack,
    Typography,
} from "@mui/material";

import StoreRoundedIcon from "@mui/icons-material/StoreRounded";
import AccessTimeRoundedIcon from "@mui/icons-material/AccessTimeRounded";
import ReceiptLongRoundedIcon from "@mui/icons-material/ReceiptLong";
import LocalDiningRoundedIcon from "@mui/icons-material/LocalDiningRounded";

import type {Order} from "../../../../domain/entities/product/order/Order";

import {formatDateTime} from "../../../utils/formatDateTime";
import {OrderStatusChip} from "../OrderStatusChip";

interface Props {
    order: Order;
}

export function ReceiptHeader({
                                  order,
                              }: Props) {

    return (

        <Paper
            square
            elevation={0}
            sx={{
                px: 4,
                py: 5,
                textAlign: "center",
                bgcolor: "background.paper",
            }}
        >

            <Stack
                sx={{
                    gap: 2,
                    alignItems: "center",
                }}
            >

                <Avatar
                    sx={{
                        width: 88,
                        height: 88,
                        bgcolor: "grey.100",
                        border: "4px solid",
                        borderColor: "background.default",
                        boxShadow: 4,
                    }}
                >
                    <StoreRoundedIcon
                        sx={{
                            fontSize: 42,
                        }}
                    />
                </Avatar>

                <Stack spacing={0.5}>

                    <Typography
                        variant="h5"
                        sx={{
                            fontWeight: 800,
                        }}
                    >
                        {order.businessName ?? "EatHub"}
                    </Typography>

                </Stack>

            </Stack>

            <Divider
                sx={{
                    my: 4,
                }}
            />

            <Stack
                sx={{
                    flexDirection: {
                        xs: "column",
                        sm: "row",
                    },
                    gap: 2,
                    justifyContent: "space-between",
                }}
            >
                <Stack
                    sx={{
                        gap: 1,
                    }}
                >
                    <Stack
                        sx={{
                            flexDirection: "row",
                            gap: 1,
                            alignItems: "center",
                        }}
                    >
                        <ReceiptLongRoundedIcon
                            fontSize="small"
                            color="action"
                        />

                        <Typography
                            sx={{
                                color: "text.secondary",
                            }}
                        >
                            سفارش
                        </Typography>

                        <Typography
                            sx={{
                                fontWeight: 800,
                            }}
                        >
                            #{order.id}
                        </Typography>

                    </Stack>

                    <Stack
                        sx={{
                            flexDirection: "row",
                            gap: 1,
                            alignItems: "center",
                        }}
                    >
                        <AccessTimeRoundedIcon
                            fontSize="small"
                            color="action"
                        />

                        <Typography
                            variant="body2"
                        >
                            {formatDateTime(order.createdAt)}
                        </Typography>

                    </Stack>

                </Stack>

                <Stack
                    sx={{
                        gap: 1,
                        alignItems: {
                            xs: "flex-start",
                            sm: "flex-end",
                        },
                    }}
                >
                    <OrderStatusChip
                        status={order.status}
                    />

                    <Stack
                        sx={{
                            flexDirection: "row",
                            gap: 1,
                            alignItems: "center",
                        }}
                    >

                        <LocalDiningRoundedIcon
                            fontSize="small"
                            color="action"
                        />

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            {order.orderType === "dine_in"
                                ? "سفارش حضوری"
                                : order.orderType === "delivery"
                                    ? "سفارش ارسال"
                                    : "سفارش بیرون‌بر"}
                        </Typography>

                    </Stack>

                </Stack>

            </Stack>

        </Paper>

    );

}