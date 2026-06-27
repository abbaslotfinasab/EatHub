import { Box, Typography } from "@mui/material";
import { FoodItemCard } from "./FoodItemCard";
import type {MenuItem} from "../../../../domain/entities/product/menu/MenuItem.ts";
import type {Menu} from "../../../../domain/entities/product/menu/Menu.ts";

type MenuSectionProps = {
    group: {
        menu:Menu
        items: MenuItem[];
    };
    search?: string;
    onItemClick?: (item: MenuItem) => void;
};

export const MenuSection = ({
    group,
    search = "",
    onItemClick,
}: MenuSectionProps) => {
    const filteredItems = group.items.filter((item) =>
        item.name
            .toLowerCase()
            .includes(search.toLowerCase())
    );

    if (!filteredItems.length) {
        return null;
    }

    return (
        <Box
            id={`menu-${group.menu.id}`}
            sx={{
                mb: 5,
            }}
        >
            {/* Category Header */}
            <Box
                sx={{
                    mb: 2.5,
                }}
            >
                <Typography
                    variant="h5"
                    sx={{
                        fontWeight: 800,
                        mb: 0.5,
                        color: "#10281A",
                    }}
                >
                    {group.menu.name}
                </Typography>

                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    {group.menu.description}

                </Typography>
            </Box>

            {/* Items */}
            <Box
                sx={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 1.5,
                }}
            >
                {filteredItems.map((item) => (
                    <FoodItemCard
                        key={item.id}
                        item={item}
                        onClick={() =>
                            onItemClick?.(item)
                        }
                    />
                ))}
            </Box>
        </Box>
    );
};