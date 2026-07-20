// presentation/components/order/OrderMenuPicker/MenuCategoryTabs.tsx

import {
    Badge,
    Chip,
    Stack,
} from "@mui/material";

import type { MenuWithItems } from "../../../../domain/entities/product/menu/MenuWithItems";

import { useOrderItems } from "./useOrderItems";

interface MenuCategoryTabsProps {
    menus: MenuWithItems[];

    selectedMenuId?: number;

    onChange: (
        menuId: number,
    ) => void;
}

export const MenuCategoryTabs = ({
    menus,
    selectedMenuId,
    onChange,
}: MenuCategoryTabsProps) => {

    const { orderItems } =
        useOrderItems();

    const getSelectedCount = (
        menu: MenuWithItems,
    ) => {

        return menu.items.reduce(
            (count, item) => {

                const selected =
                    orderItems.find(
                        x =>
                            x.menuItemId ===
                            item.id,
                    );

                return (
                    count +
                    (selected?.quantity ?? 0)
                );

            },
            0,
        );

    };

    return (

        <Stack
            useFlexGap
            sx={{
                flexDirection: "row",
                gap: 1,
                overflowX: "auto",
                pb: 1,

                "&::-webkit-scrollbar": {
                    height: 6,
                },

                "&::-webkit-scrollbar-thumb": {
                    bgcolor: "divider",
                    borderRadius: 10,
                },
            }}
        >

            {menus.map((menu) => {

                const selectedCount =
                    getSelectedCount(menu);

                return (

                    <Badge
                        key={menu.menu.id}
                        color="primary"
                        badgeContent={
                            selectedCount || null
                        }
                    >

                        <Chip
                            clickable
                            label={
                                menu.menu.name
                            }
                            color={
                                selectedMenuId ===
                                menu.menu.id
                                    ? "primary"
                                    : "default"
                            }
                            variant={
                                selectedMenuId ===
                                menu.menu.id
                                    ? "filled"
                                    : "outlined"
                            }
                            onClick={() =>
                                onChange(
                                    menu.menu.id!,
                                )
                            }
                            sx={{
                                borderRadius: 3,
                                px: 1,
                                fontWeight: 700,
                                whiteSpace:
                                    "nowrap",
                            }}
                        />

                    </Badge>

                );

            })}

        </Stack>

    );

};