import { Alert, Box, Typography } from "@mui/material";
import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../store/auth.store";
import { useBusinessContextStore } from "../store/business-context.store";
import { BusinessSwitcher } from "../components/dashboard/navbar/BusinessSwitcher";

export const BusinessGuard = () => {
    const me = useAuthStore((state) => state.me);
    const memberships = me?.memberships ?? [];
    const selectedBusinessId = useBusinessContextStore((state) => state.selectedBusinessId);
    const selectedMembershipIsValid = memberships.some(
        (membership) => membership.business_id === selectedBusinessId,
    );

    if (!me?.has_business) {
        return <Navigate to="/business" replace />;
    }

    // A stale or missing selection must never mount business-scoped routes.
    if (!selectedMembershipIsValid) {
        return (
            <Box sx={{ maxWidth: 520, mx: "auto", mt: 8, px: 2, direction: "rtl" }}>
                {memberships.length === 0 ? (
                    <Alert severity="error">
                        برای این حساب عضویت فعال و قابل‌دسترسی در هیچ کسب‌وکاری پیدا نشد.
                        لطفاً وضعیت عضویت را بررسی کنید.
                    </Alert>
                ) : (
                    <>
                        <Alert severity="info" sx={{ mb: 2 }}>
                            برای ادامه، کسب‌وکار موردنظر این تب را انتخاب کنید.
                        </Alert>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            انتخاب کسب‌وکار در تب‌های دیگر مستقل است.
                        </Typography>
                        <BusinessSwitcher />
                    </>
                )}
            </Box>
        );
    }

    return <Outlet />;
};
