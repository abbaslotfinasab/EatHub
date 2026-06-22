// src/core/presentation/components/sidebar/RestaurantSwitcher.tsx

import {
    Avatar,
    Box,
    IconButton,
    Stack,
    Tooltip,
} from "@mui/material";

import AddRoundedIcon from "@mui/icons-material/AddRounded";

import {useState} from "react";
import {useAuthStore} from "../../../store/auth.store.ts";


export const RestaurantSwitcher = () => {
    const me = useAuthStore((s) => s.me);

    const [selectedRestaurantId] =
        useState("1");


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
                sx={{
                    justifyContent: "center",
                }}
            >
                {me?.memberships.map((restaurant) => {
                    const isSelected =
                        restaurant.business_name ===
                        selectedRestaurantId;

                    return (
                        <Tooltip
                            key={me?.id}
                            title={restaurant?.business_name ?? " "}
                            arrow
                        >
                            <Avatar
                                // onClick={() =>
                                //     setSelectedRestaurantId(
                                //         restaurant.id
                                //     )
                                // }
                                // src={}
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
                                {restaurant.business_name}
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
                        <AddRoundedIcon/>
                    </IconButton>
                </Tooltip>
            </Stack>
        </Box>
    );
};