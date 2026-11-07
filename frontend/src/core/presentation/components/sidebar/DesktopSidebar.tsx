// src/core/presentation/components/sidebar/DesktopSidebar.tsx

import {useState} from "react";
import {useNavigate} from "react-router-dom";
import {Alert, Box, Collapse, Divider, Popover} from "@mui/material";

import {SidebarHeader} from "./SidebarHeader";
import {SidebarMenu} from "./SidebarMenu";
import {RestaurantList} from "./RestaurantList";
import {RestaurantSwitcherPopover} from "./RestaurantSwitcherPopover";
import {useSidebar} from "../../hooks/useSidebar";
import {SIDEBAR_WIDTH, SIDEBAR_COLLAPSED_WIDTH} from "../../../../config/constants";
import {useAuthStore} from "../../store/auth.store.ts";
import {apiClient} from "../../../data/http/http-client.ts";
import {useBusinessLogo} from "../../hooks/useBusinessLogo.ts";

export const DesktopSidebar = () => {
    const {isCollapsed} = useSidebar();
    const me = useAuthStore((s) => s.me);
    const navigate = useNavigate();
    const [restaurantMenuOpen, setRestaurantMenuOpen] = useState(false);
    const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
    const [selectingBusinessId, setSelectingBusinessId] = useState<string | null>(null);
    const [switchError, setSwitchError] = useState("");

    const restaurants = me?.memberships?.map((membership) => ({
        id: String(membership.business_id),
        name: membership.business_name,
        logo: "🏪",
    })) ?? [];
    const restaurantLogo = useBusinessLogo(me?.active_business?.id ?? null);
    const selectedRestaurantId = me?.active_business
        ? String(me.active_business.id)
        : "";

    const handleHeaderClick = (event: React.MouseEvent<HTMLElement>) => {
        if (isCollapsed) {
            setAnchorEl(event.currentTarget);
            return;
        }
        setRestaurantMenuOpen((previous) => !previous);
    };

    const handleClosePopover = () => setAnchorEl(null);

    const handleSelectBusiness = async (id: string) => {
        if (id === selectedRestaurantId || selectingBusinessId) {
            setRestaurantMenuOpen(false);
            handleClosePopover();
            return;
        }

        setSwitchError("");
        setSelectingBusinessId(id);
        try {
            await apiClient.post("/accounts/auth/select-business/", {
                business_id: Number(id),
            });
            // A full app reload clears business-scoped query caches and hydrates
            // the newly selected tenant context from /auth/me/.
            window.location.assign("/dashboard");
        } catch {
            setSwitchError("تغییر کسب‌وکار انجام نشد. دوباره تلاش کنید.");
            setSelectingBusinessId(null);
        }
    };

    const handleAddBusiness = () => {
        setRestaurantMenuOpen(false);
        handleClosePopover();
        navigate("/business");
    };

    return (
        <>
            <Box sx={{
                position: "fixed", top: 0, right: 0,
                width: isCollapsed ? SIDEBAR_COLLAPSED_WIDTH : SIDEBAR_WIDTH,
                height: "100vh", bgcolor: "#10281A",
                borderLeft: "1px solid rgba(255,255,255,.05)",
                transition: "all .3s ease", zIndex: 1200,
                display: "flex", flexDirection: "column", overflow: "hidden",
            }}>
                <SidebarHeader
                    restaurantName={me?.active_business?.name}
                    restaurantRole={me?.active_business?.role}
                    restaurantLogo={restaurantLogo}
                    isOpen={restaurantMenuOpen}
                    onToggle={handleHeaderClick}
                />

                {switchError && (
                    <Alert severity="error" onClose={() => setSwitchError("")}>
                        {switchError}
                    </Alert>
                )}

                {!isCollapsed && (
                    <Collapse in={restaurantMenuOpen}>
                        <RestaurantList
                            restaurants={restaurants}
                            selectedRestaurantId={selectedRestaurantId}
                            onSelect={handleSelectBusiness}
                            onAddRestaurant={handleAddBusiness}
                        />
                    </Collapse>
                )}

                <Divider sx={{borderColor: "rgba(255,255,255,.08)"}} />

                <Box sx={{flex: 1, overflowY: "auto", overflowX: "hidden", py: 1}}>
                    <SidebarMenu/>
                </Box>
            </Box>

            <Popover
                open={Boolean(anchorEl)}
                anchorEl={anchorEl}
                onClose={handleClosePopover}
                anchorOrigin={{vertical: "center", horizontal: "left"}}
                transformOrigin={{vertical: "center", horizontal: "right"}}
                slotProps={{paper: {sx: {bgcolor: "transparent", boxShadow: "none"}}}}
            >
                <RestaurantSwitcherPopover
                    restaurants={restaurants}
                    selectedRestaurantId={selectedRestaurantId}
                    onAddRestaurant={handleAddBusiness}
                    onSelect={handleSelectBusiness}
                />
            </Popover>
        </>
    );
};
