// presentation/components/order/OrderMenuPicker/MenuItemCard.tsx

import {
    Avatar,
    Chip,
    Paper,
    Stack,
    Typography,
} from "@mui/material";

import type {MenuItem} from "../../../../domain/entities/product/menu/MenuItem";

import {useOrderItems} from "./useOrderItems";

import {MenuItemQuantity} from "./MenuItemQuantity";
import {formatCurrency} from "../../../utils/formatCurrency.ts";

interface MenuItemCardProps {
    item: MenuItem;
}

export const MenuItemCard = ({
                                 item,
                             }: MenuItemCardProps) => {

    const {
        orderItems,
        addItem,
        increaseQuantity,
        decreaseQuantity,
    } = useOrderItems();

    const selectedItem =
        orderItems.find(
            x => x.menuItemId === item.id,
        );

    const quantity =
        selectedItem?.quantity ?? 0;

    return (

        <Paper
            variant="outlined"
            sx={{
                p: 2,
                borderRadius: 3,

                transition: ".2s",

                borderColor:
                    quantity > 0
                        ? "primary.main"
                        : "divider",

                bgcolor:
                    quantity > 0
                        ? "primary.50"
                        : "background.paper",

                "&:hover": {
                    borderColor:
                        "primary.main",
                    boxShadow: 2,
                },
            }}
        >

            <Stack
                sx={{
                    flexDirection: "row",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: 2,
                }}
            >

                <Stack
                    sx={{
                        flexDirection: "row",
                        gap: 2,
                        alignItems: "center",
                    }}
                >

                    <Avatar
                        src={
                            item.imageUrl ??
                            ""
                        }
                        variant="rounded"
                        sx={{
                            width: 72,
                            height: 72,
                            borderRadius: 2,
                        }}
                    >
                        {item.name[0]}
                    </Avatar>

                    <Stack spacing={0.5}>

                        <Typography
                            sx={{
                                fontWeight: 700,
                            }}
                        >
                            {item.name}
                        </Typography>

                        {item.description && (

                            <Typography
                                variant="body2"
                                color="text.secondary"
                            >
                                {
                                    item.description
                                }
                            </Typography>

                        )}

                        <Stack
                            sx={{
                                flexDirection: "row",
                                gap: 1,
                                alignItems: "center",
                            }}
                        >

                            <Typography
                                color="primary"
                                sx={{
                                    fontWeight: 700,
                                }}
                            >
                                {formatCurrency(
                                    item.price,
                                )}
                            </Typography>

                            {!item.isAvailable && (

                                <Chip
                                    size="small"
                                    color="error"
                                    label="ناموجود"
                                />

                            )}

                        </Stack>

                    </Stack>

                </Stack>

                {item.isAvailable && (

                    <MenuItemQuantity
                        quantity={
                            quantity
                        }
                        onAdd={() =>
                            addItem(
                                item,
                            )
                        }
                        onIncrease={() =>
                            increaseQuantity(
                                item.id,
                            )
                        }
                        onDecrease={() =>
                            decreaseQuantity(
                                item.id,
                            )
                        }
                    />

                )}

            </Stack>

        </Paper>

    );

};