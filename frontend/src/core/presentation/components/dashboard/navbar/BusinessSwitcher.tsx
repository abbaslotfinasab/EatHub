import { useEffect } from "react";
import { FormControl, MenuItem, Select, Typography } from "@mui/material";
import { useAuthStore } from "../../store/auth.store.ts";
import { useBusinessContextStore } from "../../store/business-context.store.ts";

export const BusinessSwitcher = () => {
    const memberships = useAuthStore((state) => state.me?.memberships ?? []);
    const selectedBusinessId = useBusinessContextStore((state) => state.selectedBusinessId);
    const selectBusiness = useBusinessContextStore((state) => state.selectBusiness);

    useEffect(() => {
        const selectedIsAvailable = memberships.some(
            (membership) => membership.business_id === selectedBusinessId,
        );
        if (selectedBusinessId !== null && !selectedIsAvailable) {
            selectBusiness(null);
            return;
        }
        // A single eligible membership is unambiguous; multiple memberships always
        // require an explicit choice in this tab.
        if (selectedBusinessId === null && memberships.length === 1) {
            selectBusiness(memberships[0].business_id);
        }
    }, [memberships, selectedBusinessId, selectBusiness]);

    if (memberships.length === 0) return null;

    return (
        <FormControl size="small" sx={{ minWidth: { xs: 132, sm: 190 } }}>
            <Select
                value={selectedBusinessId ?? ""}
                displayEmpty
                onChange={(event) => {
                    const value = event.target.value;
                    selectBusiness(value === "" ? null : Number(value));
                }}
                inputProps={{ "aria-label": "انتخاب کسب‌وکار" }}
                renderValue={(value) => {
                    if (!value) return <Typography variant="body2" color="text.secondary">انتخاب کسب‌وکار</Typography>;
                    return memberships.find((item) => item.business_id === Number(value))?.business_name ?? "انتخاب کسب‌وکار";
                }}
                sx={{ borderRadius: 2, bgcolor: "#F9FAFB", fontSize: 14 }}
            >
                {memberships.map((membership) => (
                    <MenuItem key={membership.business_id} value={membership.business_id}>
                        {membership.business_name} · {membership.role}
                    </MenuItem>
                ))}
            </Select>
        </FormControl>
    );
};
