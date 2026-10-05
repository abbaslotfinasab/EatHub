import {useMemo} from "react";

import {
    CircularProgress,
    Alert,
    Button,
    Stack,
    Typography,
    Paper,
} from "@mui/material";


import {SelectedOrderItemCard} from "./SelectedOrderItemCard.tsx";
import {EmptySelectedItems} from "./EmptySelectedItems.tsx";
import {useGetMenus} from "../../hooks/menu/useGetMenus.ts";
import {useOrderItems} from "../../forms/order/useOrderItems.ts";
import type {OrderItem} from "../../../domain/entities/product/order/OrderItem.ts";
import {formatCurrency} from "../../utils/formatCurrency.ts";

interface SelectedOrderItemsProps {
    historicalItems?: OrderItem[];
    onRemoveHistorical?: (item: OrderItem) => void;
}

export const SelectedOrderItems = ({
    historicalItems = [],
    onRemoveHistorical,
}: SelectedOrderItemsProps) => {

    const {
        data: menus = [],
        isLoading,
    } = useGetMenus();

    const {
        orderItems,
        increaseQuantity,
        decreaseQuantity,
        removeItem,
    } = useOrderItems();

    // ==========================
    // Flatten Menu Items
    // ==========================

    const menuItems = useMemo(() => {

        return menus.flatMap(
            menu => menu.items,
        );

    }, [menus]);

    // ==========================
    // Merge Form + Menu
    // ==========================

    const items = useMemo(() => {

        return orderItems
            .map(item => {

                const menuItem =
                    menuItems.find(
                        menu =>
                            menu.id ===
                            item.menuItemId,
                    );

                if (!menuItem) {
                    return null;
                }

                return {
                    item,
                    menuItem,
                };

            })
            .filter(Boolean);

    }, [
        orderItems,
        menuItems,
    ]);

    // ==========================

    if (isLoading) {
        return (
            <Stack
                sx={{
                    alignItems: "center",
                    py: 8,
                }}
            >
                <CircularProgress/>
            </Stack>
        );
    }

    // ==========================

    if (items.length === 0 && historicalItems.length === 0) {
        return <EmptySelectedItems/>;
    }

    // ==========================

    return (

        <Stack spacing={2}>

            <Typography
                variant="h6"
                sx={{
                    fontWeight: 700,
                }}
            >
                سفارش جاری
            </Typography>

            {historicalItems.length > 0 && (
                <Alert
                    severity="warning"
                    action={null}
                >
                    آیتم‌های تاریخی قابل ارسال نیستند؛ برای ادامه، هر آیتم را با
                    یک آیتم فعلی جایگزین کنید.
                </Alert>
            )}

            {historicalItems.map((item) => (
                <Paper
                    key={`historical-${item.id ?? item.orderId}`}
                    variant="outlined"
                    sx={{
                        p: 2,
                        borderRadius: 3,
                        borderColor: "warning.main",
                    }}
                >
                    <Stack spacing={1}>
                        <Stack
                            direction="row"
                            justifyContent="space-between"
                            alignItems="center"
                            gap={2}
                        >
                            <Typography fontWeight={700}>
                                {item.menuItemName ?? "آیتم تاریخی"}
                            </Typography>
                            <Typography
                                variant="caption"
                                color="warning.dark"
                                fontWeight={700}
                            >
                                آیتم تاریخی
                            </Typography>
                        </Stack>
                        <Typography variant="body2" color="text.secondary">
                            {item.quantity} × {formatCurrency(item.unitPrice ?? 0)}
                            {" — "}
                            {formatCurrency(item.totalPrice ?? 0)}
                        </Typography>
                        {onRemoveHistorical && (
                            <Button
                                color="warning"
                                size="small"
                                onClick={() => onRemoveHistorical(item)}
                            >
                                حذف آیتم تاریخی و جایگزینی دستی
                            </Button>
                        )}
                    </Stack>
                </Paper>
            ))}

            {items.map(data => {

                if (!data) return null;

                return (
                    <SelectedOrderItemCard
                        key={data.menuItem.id}
                        menuItem={data.menuItem}
                        item={data.item}
                        onIncrease={() =>
                            increaseQuantity(
                                data.menuItem.id ?? -1,
                            )
                        }
                        onDecrease={() =>
                            decreaseQuantity(
                                data.menuItem.id ?? -1,
                            )
                        }
                        onRemove={() =>
                            removeItem(
                                data.menuItem.id ?? -1,
                            )
                        }
                    />
                );

            })}

        </Stack>

    );

};
