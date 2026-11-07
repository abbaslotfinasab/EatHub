import { useEffect, useState } from "react";
import { Alert, Box, CircularProgress, FormControlLabel, Paper, Switch, Typography } from "@mui/material";
import { apiClient } from "../../data/http/http-client";

export const InventorySettingsPage = () => {
    const [enabled, setEnabled] = useState(true);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    useEffect(() => {
        let active = true;
        apiClient.get("/accounts/business/inventory-settings/")
            .then(({ data }) => { if (active) setEnabled(Boolean(data.inventory_enabled)); })
            .catch(() => { if (active) setError("دریافت تنظیمات انبارداری ناموفق بود."); })
            .finally(() => { if (active) setLoading(false); });
        return () => { active = false; };
    }, []);

    const handleChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const next = event.target.checked;
        setSaving(true);
        setError("");
        try {
            await apiClient.patch("/accounts/business/inventory-settings/", { inventory_enabled: next });
            setEnabled(next);
        } catch (e: any) {
            setError(e?.response?.data?.detail || "ذخیره تنظیمات ناموفق بود. تغییر این گزینه فقط برای مالک کسب‌وکار مجاز است.");
        } finally {
            setSaving(false);
        }
    };

    return (
        <Box sx={{ maxWidth: 760, mx: "auto" }}>
            <Typography variant="h5" fontWeight={700} mb={2}>تنظیمات انبارداری</Typography>
            <Paper variant="outlined" sx={{ p: 3, borderRadius: 3 }}>
                <Typography fontWeight={700} mb={1}>اتصال سفارش‌ها به انبار</Typography>
                <Typography color="text.secondary" mb={2}>
                    با فعال‌بودن انبارداری، تأیید سفارش بر اساس رسپی، انبار پیش‌فرض و موجودی کالا انجام می‌شود.
                    در حالت غیرفعال، سفارش‌ها بدون ثبت رزرو و مصرف موجودی مدیریت می‌شوند.
                </Typography>
                {loading ? <CircularProgress size={24} /> : (
                    <FormControlLabel
                        control={<Switch checked={enabled} onChange={handleChange} disabled={saving} />}
                        label={enabled ? "انبارداری فعال است" : "فقط مدیریت سفارش فعال است"}
                    />
                )}
                {saving && <Typography variant="caption" display="block">در حال ذخیره…</Typography>}
                {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
                <Alert severity="info" sx={{ mt: 2 }}>
                    غیرفعال‌کردن این گزینه، سوابق و رزروهای سفارش‌هایی را که قبلاً با انبارداری تأیید شده‌اند حذف نمی‌کند.
                </Alert>
            </Paper>
        </Box>
    );
};
