// presentation/components/order/OrderMenuPicker/MenuItemsList.tsx

import {
    Stack,
    Typography,
} from "@mui/material";

import type { MenuWithItems } from "../../../../domain/entities/product/menu/MenuWithItems";

import { MenuItemCard } from "./MenuItemCard";

interface MenuItemsListProps {
    menu: MenuWithItems;
}

export const MenuItemsList = ({
    menu,
}: MenuItemsListProps) => {

    if (menu.items.length === 0) {
        return (
            <Stack
                sx={{
                    py: 6,
                    alignItems: "center",
                    justifyContent: "center",
                }}
            >
                <Typography color="text.secondary">
                    آیتمی در این دسته وجود ندارد.
                </Typography>
            </Stack>
        );
    }

    return (
        <Stack spacing={2}>

            {menu.items.map((item) => (

                <MenuItemCard
                    key={item.id}
                    item={item}
                />

            ))}

        </Stack>
    );
};