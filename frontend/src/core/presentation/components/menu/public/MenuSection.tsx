import { Box, Typography } from "@mui/material";
import { FoodItemCard } from "./FoodItemCard";

type MenuSectionProps = {
    group: {
        menu: {
            id: string;
            name: string;
        };
        items: any[];
    };
    search?: string;
    onItemClick?: (item: any) => void;
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
                    {filteredItems.length} item
                    {filteredItems.length > 1 ? "s" : ""}
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