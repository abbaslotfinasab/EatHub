// src/core/presentation/components/sidebar/DesktopSidebar.tsx

import { useState } from "react";

import {
    Box,
    Collapse,
    Divider,
    Popover,
} from "@mui/material";

import { SidebarHeader } from "./SidebarHeader";
import { SidebarMenu } from "./SidebarMenu";
import { RestaurantList } from "./RestaurantList";
import { RestaurantSwitcherPopover } from "./RestaurantSwitcherPopover";

import { useSidebar } from "../../hooks/useSidebar";

import {
    SIDEBAR_WIDTH,
    SIDEBAR_COLLAPSED_WIDTH,
} from "../../../../config/constants";

export const DesktopSidebar = () => {
    const { isCollapsed } = useSidebar();

    const [restaurantMenuOpen, setRestaurantMenuOpen] =
        useState(false);

    const [anchorEl, setAnchorEl] =
        useState<HTMLElement | null>(null);

    const [selectedRestaurantId, setSelectedRestaurantId] =
        useState("1");

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

    const handleHeaderClick = (
        event: React.MouseEvent<HTMLElement>
    ) => {
        if (isCollapsed) {
            setAnchorEl(event.currentTarget);
            return;
        }

        setRestaurantMenuOpen(
            (prev) => !prev
        );
    };

    const handleClosePopover = () => {
        setAnchorEl(null);
    };

    return (
        <>
            <Box
                sx={{
                    position: "fixed",
                    top: 0,
                    right: 0,

                    width: isCollapsed
                        ? SIDEBAR_COLLAPSED_WIDTH
                        : SIDEBAR_WIDTH,

                    height: "100vh",

                    bgcolor: "#10281A",

                    borderLeft:
                        "1px solid rgba(255,255,255,.05)",

                    transition: "all .3s ease",

                    zIndex: 1200,

                    display: "flex",
                    flexDirection: "column",

                    overflow: "hidden",
                }}
            >
                <SidebarHeader
                    restaurantName={
                        selectedRestaurant.name
                    }
                    isOpen={
                        restaurantMenuOpen
                    }
                    onToggle={
                        handleHeaderClick
                    }
                />

                {!isCollapsed && (
                    <Collapse
                        in={
                            restaurantMenuOpen
                        }
                    >
                        <RestaurantList
                            restaurants={
                                restaurants
                            }
                            selectedRestaurantId={
                                selectedRestaurantId
                            }
                            onSelect={(id) => {
                                setSelectedRestaurantId(
                                    id
                                );

                                setRestaurantMenuOpen(
                                    false
                                );
                            }}
                            onAddRestaurant={() => {
                                console.log(
                                    "add restaurant"
                                );
                            }}
                        />
                    </Collapse>
                )}

                <Divider
                    sx={{
                        borderColor:
                            "rgba(255,255,255,.08)",
                    }}
                />

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

            {/* Collapsed Mode Restaurant Switcher */}

            <Popover
                open={Boolean(anchorEl)}
                anchorEl={anchorEl}
                onClose={
                    handleClosePopover
                }
                anchorOrigin={{
                    vertical: "center",
                    horizontal: "left",
                }}
                transformOrigin={{
                    vertical: "center",
                    horizontal: "right",
                }}
                PaperProps={{
                    sx: {
                        bgcolor: "transparent",
                        boxShadow: "none",
                    },
                }}
            >
                <RestaurantSwitcherPopover
                    restaurants={
                        restaurants
                    }
                    selectedRestaurantId={
                        selectedRestaurantId
                    }
                    onSelect={(id) => {
                        setSelectedRestaurantId(
                            id
                        );

                        handleClosePopover();
                    }}
                />
            </Popover>
        </>
    );
};