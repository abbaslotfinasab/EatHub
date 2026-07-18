import {useMemo} from "react";

import {
    CircularProgress,
    Stack,
    Typography,
} from "@mui/material";


import {SelectedOrderItemCard} from "./SelectedOrderItemCard.tsx";
import {EmptySelectedItems} from "./EmptySelectedItems.tsx";
import {useGetMenus} from "../../hooks/menu/useGetMenus.ts";
import {useOrderItems} from "../../forms/order/useOrderItems.ts";

export const SelectedOrderItems = () => {

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

    if (items.length === 0) {
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