import { Alert, Box, Typography } from "@mui/material";
import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../store/auth.store";
import { useBusinessContextStore } from "../store/business-context.store";
import { BusinessSwitcher } from "../components/dashboard/navbar/BusinessSwitcher";

export const BusinessGuard = () => {
    const me = useAuthStore((state) => state.me);
    const selectedBusinessId = useBusinessContextStore((state) => state.selectedBusinessId);

    if (!me?.has_business) {
        return <Navigate to="/business" replace />;
    }

    // Never guess between multiple memberships. Require an explicit choice in this tab.
    if (me.memberships.length > 1 && selectedBusinessId === null) {
        return (
            <Box sx={{ maxWidth: 520, mx: "auto", mt: 8, px: 2, direction: "rtl" }}>
                <Alert severity="info" sx={{ mb: 2 }}>
                    برای ادامه، کسب‌وکار موردنظر این تب را انتخاب کنید.
                </Alert>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    انتخاب کسب‌وکار در تب‌های دیگر مستقل است.
                </Typography>
                <BusinessSwitcher />
            </Box>
        );
    }

    return <Outlet />;
};
