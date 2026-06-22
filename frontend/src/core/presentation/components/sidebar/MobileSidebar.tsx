import {useState} from "react";

import {
    Box,
    Collapse,
    Divider,
    Drawer,
} from "@mui/material";

import {SidebarHeader} from "./SidebarHeader";
import {SidebarMenu} from "./SidebarMenu";
import {RestaurantList} from "./RestaurantList";

import {useSidebar} from "../../hooks/useSidebar";

import {
    SIDEBAR_WIDTH,
} from "../../../../config/constants";

import {useAuthStore} from "../../../store/auth.store";

export const MobileSidebar = () => {
    const {
        mobileOpen,
        closeMobile,
    } = useSidebar();

    const me = useAuthStore((s) => s.me);

    const restaurants =
        me?.memberships?.map((m) => ({
            id: String(m.business_id),
            name: m.business_name,
            logo: "🏪",
        })) ?? [];

    const [restaurantMenuOpen, setRestaurantMenuOpen] =
        useState(false);

    const [selectedRestaurantId, setSelectedRestaurantId] =
        useState(
            me?.active_business?.id
                ? String(
                    me.active_business.id
                )
                : ""
        );

    return (
        <Drawer
            anchor="right"
            open={mobileOpen}
            onClose={closeMobile}
            ModalProps={{
                keepMounted: true,
            }}
            slotProps={{
                paper: {
                    sx: {
                        width: SIDEBAR_WIDTH,
                        bgcolor: "#10281A",
                        color: "#fff",

                        display: "flex",
                        flexDirection: "column",

                        overflow: "hidden",
                    },
                },
            }}
        >
            <SidebarHeader
                restaurantName={
                    me?.active_business?.name
                }
                restaurantRole={
                    me?.active_business?.role
                }
                isOpen={
                    restaurantMenuOpen
                }
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

            <Collapse
                in={restaurantMenuOpen}
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

                        closeMobile();
                    }}
                    onAddRestaurant={() => {
                        console.log(
                            "add restaurant"
                        );
                    }}
                />
            </Collapse>

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

                    "&::-webkit-scrollbar":
                        {
                            width: 6,
                        },

                    "&::-webkit-scrollbar-thumb":
                        {
                            background:
                                "rgba(255,255,255,.12)",

                            borderRadius: 20,
                        },
                }}
            >
                <SidebarMenu/>
            </Box>

            <Box
                sx={{
                    p: 2,

                    borderTop:
                        "1px solid rgba(255,255,255,.08)",

                    bgcolor:
                        "rgba(255,255,255,.02)",
                }}
            >
                <Box
                    sx={{
                        px: 2,
                        py: 1.5,

                        borderRadius: 3,

                        bgcolor:
                            "rgba(255,255,255,.05)",

                        border:
                            "1px solid rgba(255,255,255,.08)",
                    }}
                >
                    <Box
                        sx={{
                            fontSize: 12,

                            opacity: 0.7,

                            mb: 0.5,
                        }}
                    >
                        کسب‌وکار فعال
                    </Box>

                    <Box
                        sx={{
                            fontWeight: 700,

                            overflow:
                                "hidden",

                            textOverflow:
                                "ellipsis",

                            whiteSpace:
                                "nowrap",
                        }}
                    >
                        {
                            me
                                ?.active_business
                                ?.name
                        }
                    </Box>
                </Box>
            </Box>
        </Drawer>
    );
};