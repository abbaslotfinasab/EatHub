// src/core/presentation/components/sidebar/RestaurantSwitcher.tsx

import {
    Avatar,
    Box,
    IconButton,
    Stack,
    Tooltip,
} from "@mui/material";

import AddRoundedIcon from "@mui/icons-material/AddRounded";

import { useState } from "react";

interface Restaurant {
    id: string;
    name: string;
    logo?: string;
}

export const RestaurantSwitcher = () => {
    const [selectedRestaurantId, setSelectedRestaurantId] =
        useState("1");

    const restaurants: Restaurant[] = [
        {
            id: "1",
            name: "پیتزا میلان",
        },
        {
            id: "2",
            name: "برگر هاب",
        },
        {
            id: "3",
            name: "کافه روم",
        },
    ];

    return (
        <Box
            sx={{
                py: 2,
                px: 1,
            }}
        >
            <Stack
                direction="row"
                spacing={1}
                justifyContent="center"
            >
                {restaurants.map((restaurant) => {
                    const isSelected =
                        restaurant.id ===
                        selectedRestaurantId;

                    return (
                        <Tooltip
                            key={restaurant.id}
                            title={restaurant.name}
                            arrow
                        >
                            <Avatar
                                onClick={() =>
                                    setSelectedRestaurantId(
                                        restaurant.id
                                    )
                                }
                                src={restaurant.logo}
                                sx={{
                                    width: 52,
                                    height: 52,
                                    cursor: "pointer",

                                    bgcolor: isSelected
                                        ? "#10281A"
                                        : "#E5E7EB",

                                    color: isSelected
                                        ? "#FFFFFF"
                                        : "#374151",

                                    border: isSelected
                                        ? "3px solid #22C55E"
                                        : "3px solid transparent",

                                    transition:
                                        "all .2s ease",

                                    "&:hover": {
                                        transform:
                                            "scale(1.08)",
                                    },
                                }}
                            >
                                {restaurant.name[0]}
                            </Avatar>
                        </Tooltip>
                    );
                })}

                <Tooltip
                    title="افزودن رستوران"
                    arrow
                >
                    <IconButton
                        sx={{
                            width: 52,
                            height: 52,

                            border: "2px dashed #CBD5E1",

                            borderRadius: "50%",

                            color: "#64748B",

                            "&:hover": {
                                bgcolor: "#F8FAFC",
                            },
                        }}
                    >
                        <AddRoundedIcon />
                    </IconButton>
                </Tooltip>
            </Stack>
        </Box>
    );
};