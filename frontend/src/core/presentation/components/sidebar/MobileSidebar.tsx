// src/core/presentation/components/sidebar/MobileSidebar.tsx

import {
    Drawer,
    Box,
    Divider, Collapse,
} from "@mui/material";

import { SidebarHeader } from "./SidebarHeader";
import { RestaurantList } from "./RestaurantList";
import { SidebarMenu } from "./SidebarMenu";

import { useSidebar } from "../../hooks/useSidebar";

import {
    SIDEBAR_WIDTH,
} from "../../../../config/constants";

import { useState } from "react";

export const MobileSidebar = () => {
    const {
        mobileOpen,
        closeMobile,
    } = useSidebar();

    const [selectedRestaurantId, setSelectedRestaurantId] =
        useState("1");

    const [restaurantMenuOpen, setRestaurantMenuOpen] =
        useState(false);

    const restaurants = [
        {
            id: "1",
            name: "پیتزا هاب",
            emoji: "🍕",
        },
        {
            id: "2",
            name: "برگر هاب",
            emoji: "🍔",
        },
        {
            id: "3",
            name: "کافه هاب",
            emoji: "☕",
        },
        {
            id: "4",
            name: "کافه مرکزی",
            emoji: "🥗",
        },
    ];

    const selectedRestaurant =
        restaurants.find(
            (r) => r.id === selectedRestaurantId
        ) ?? restaurants[0];

    return (
        <Drawer
            anchor="right"
            open={mobileOpen}
            onClose={closeMobile}
            ModalProps={{
                keepMounted: true,
            }}
            PaperProps={{
                sx: {
                    width: SIDEBAR_WIDTH,
                    bgcolor: "#10281A",
                    color: "#FFFFFF",
                    overflow: "hidden",
                },
            }}
        >
            <Box
                sx={{
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                }}
            >
                {/* Header */}

                <SidebarHeader
                    restaurantName={
                        selectedRestaurant.name
                    }
                    isOpen={restaurantMenuOpen}
                    onToggle={() =>
                        setRestaurantMenuOpen(
                            (prev) => !prev
                        )
                    }
                />

                <Divider
                    sx={{
                        borderColor:
                            "rgba(255,255,255,.08)",
                    }}
                />

                {/* Restaurant List */}

                <Collapse in={restaurantMenuOpen}>
                    <RestaurantList
                        restaurants={restaurants}
                        selectedRestaurantId={selectedRestaurantId}
                        onSelect={(id) => {
                            setSelectedRestaurantId(id);
                        }}
                        onAddRestaurant={() => {
                            console.log("add restaurant");
                        }}
                    />
                </Collapse>

                <Divider
                    sx={{
                        borderColor:
                            "rgba(255,255,255,.08)",
                    }}
                />

                {/* Menu */}

                <Box
                    sx={{
                        flex: 1,
                        overflowY: "auto",
                        overflowX: "hidden",
                        py: 1,
                    }}
                >
                    <SidebarMenu />
                </Box>
            </Box>
        </Drawer>
    );
};