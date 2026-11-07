import {useState} from "react";
import {useNavigate} from "react-router-dom";
import {Alert, Box, Collapse, Divider, Drawer} from "@mui/material";
import {SidebarHeader} from "./SidebarHeader";
import {SidebarMenu} from "./SidebarMenu";
import {RestaurantList} from "./RestaurantList";
import {useSidebar} from "../../hooks/useSidebar";
import {SIDEBAR_WIDTH} from "../../../../config/constants";
import {useAuthStore} from "../../store/auth.store";
import {apiClient} from "../../../data/http/http-client.ts";

export const MobileSidebar = () => {
    const {mobileOpen, closeMobile} = useSidebar();
    const me = useAuthStore((state) => state.me);
    const navigate = useNavigate();
    const [restaurantMenuOpen, setRestaurantMenuOpen] = useState(false);
    const [switchError, setSwitchError] = useState("");
    const [selectingBusinessId, setSelectingBusinessId] = useState<string | null>(null);

    const restaurants = me?.memberships?.map((membership) => ({
        id: String(membership.business_id),
        name: membership.business_name,
        logo: "🏪",
    })) ?? [];
    const selectedRestaurantId = me?.active_business
        ? String(me.active_business.id)
        : "";

    const selectBusiness = async (id: string) => {
        if (id === selectedRestaurantId || selectingBusinessId) {
            setRestaurantMenuOpen(false);
            closeMobile();
            return;
        }
        setSwitchError("");
        setSelectingBusinessId(id);
        try {
            await apiClient.post("/accounts/auth/select-business/", {business_id: Number(id)});
            window.location.assign("/dashboard");
        } catch {
            setSwitchError("تغییر کسب‌وکار انجام نشد. دوباره تلاش کنید.");
            setSelectingBusinessId(null);
        }
    };

    return (
        <Drawer
            anchor="right"
            open={mobileOpen}
            onClose={closeMobile}
            ModalProps={{keepMounted: true}}
            slotProps={{paper: {
                sx: {
                    width: SIDEBAR_WIDTH, bgcolor: "#10281A", color: "#fff",
                    display: "flex", flexDirection: "column", overflow: "hidden",
                },
            }}}
        >
            <SidebarHeader
                restaurantName={me?.active_business?.name}
                restaurantRole={me?.active_business?.role}
                restaurantLogo={me?.active_business?.logo ?? undefined}
                isOpen={restaurantMenuOpen}
                onToggle={() => setRestaurantMenuOpen((previous) => !previous)}
            />

            {switchError && <Alert severity="error" onClose={() => setSwitchError("")}>{switchError}</Alert>}
            <Divider sx={{borderColor: "rgba(255,255,255,.08)"}} />

            <Collapse in={restaurantMenuOpen}>
                <RestaurantList
                    restaurants={restaurants}
                    selectedRestaurantId={selectedRestaurantId}
                    onSelect={selectBusiness}
                    onAddRestaurant={() => {
                        setRestaurantMenuOpen(false);
                        closeMobile();
                        navigate("/business");
                    }}
                />
            </Collapse>

            <Divider sx={{borderColor: "rgba(255,255,255,.08)"}} />
            <Box sx={{
                flex: 1, overflowY: "auto", overflowX: "hidden", py: 1,
                "&::-webkit-scrollbar": {width: 6},
                "&::-webkit-scrollbar-thumb": {background: "rgba(255,255,255,.12)", borderRadius: 20},
            }}>
                <SidebarMenu/>
            </Box>

            <Box sx={{p: 2, borderTop: "1px solid rgba(255,255,255,.08)", bgcolor: "rgba(255,255,255,.02)"}}>
                <Box sx={{px: 2, py: 1.5, borderRadius: 3, bgcolor: "rgba(255,255,255,.05)", border: "1px solid rgba(255,255,255,.08)"}}>
                    <Box sx={{fontSize: 12, opacity: 0.7, mb: 0.5}}>کسب‌وکار فعال</Box>
                    <Box sx={{fontWeight: 700, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap"}}>
                        {me?.active_business?.name}
                    </Box>
                </Box>
            </Box>
        </Drawer>
    );
};
