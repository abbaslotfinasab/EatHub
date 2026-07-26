import {
    Divider,
    Stack,
    Typography,
} from "@mui/material";

import LocalDiningRoundedIcon from "@mui/icons-material/LocalDiningRounded";
import type {OrderItem} from "../../../../domain/entities/product/order/OrderItem.ts";
import { formatCurrency } from "../../../utils/formatCurrency.ts";



interface ReceiptItemsProps {
    items: OrderItem[];
}

export function ReceiptItems({
    items,
}: ReceiptItemsProps) {

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

            <LocalDiningRoundedIcon
                color="primary"
            />

            <Typography
                variant="h6"
                sx={{
                    fontWeight: 700,
                }}
            >
                اقلام سفارش
            </Typography>

        </Stack>

        <Divider />

        <Stack
            sx={{
                gap: 2,
            }}
        >

            {items.map((item, index) => (

                <Stack
                    key={item.id}
                    sx={{
                        gap: 1.5,
                    }}
                >

                    <Stack
                        sx={{
                            flexDirection: "row",
                            justifyContent: "space-between",
                            alignItems: "flex-start",
                        }}
                    >

                        <Stack
                            sx={{
                                gap: 0.5,
                            }}
                        >

                            <Typography
                                sx={{
                                    fontWeight: 700,
                                }}
                            >
                                {item.menuItemName}
                            </Typography>

                            {item.notes && (

                                <Typography
                                    variant="caption"
                                    sx={{
                                        color: "text.secondary",
                                    }}
                                >
                                    {item.notes}
                                </Typography>

                            )}

                        </Stack>

                        <Typography
                            sx={{
                                fontWeight: 700,
                                color: "primary.main",
                            }}
                        >
                            {formatCurrency(item.totalPrice ?? 0)}
                        </Typography>

                    </Stack>

                    <Stack
                        sx={{
                            flexDirection: "row",
                            justifyContent: "space-between",
                        }}
                    >

                        <Typography
                            variant="body2"
                            sx={{
                                color: "text.secondary",
                            }}
                        >
                            {item.quantity} × {formatCurrency(item.unitPrice ?? 0)}
                        </Typography>

                        <Typography
                            variant="body2"
                            sx={{
                                color: "text.secondary",
                            }}
                        >
                            تعداد {item.quantity}
                        </Typography>

                    </Stack>

                    {index !== items.length - 1 && (
                        <Divider />
                    )}

                </Stack>

            ))}

        </Stack>

    </Stack>

);

}