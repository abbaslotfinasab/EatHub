import { useEffect, useState } from "react";
import type { ChangeEvent } from "react";
import { Alert, Box, Button, CircularProgress, Dialog, DialogContent, DialogTitle, FormControlLabel, Paper, Stack, Switch, Typography } from "@mui/material";
import { apiClient } from "../../data/http/http-client";
import { WarehousesPage } from "./WarehousesPage";

export const InventorySettingsSection = ({embedded = false}: {embedded?: boolean}) => {
    const [enabled, setEnabled] = useState(true);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [warehousesOpen, setWarehousesOpen] = useState(false);

    useEffect(() => {
        let active = true;
        apiClient.get("/accounts/business/inventory-settings/")
            .then(({ data }) => { if (active) setEnabled(Boolean(data.inventory_enabled)); })
            .catch(() => { if (active) setError("دریافت تنظیمات انبارداری ناموفق بود."); })
            .finally(() => { if (active) setLoading(false); });
        return () => { active = false; };
    }, []);

    const handleChange = async (event: ChangeEvent<HTMLInputElement>) => {
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
        <Box sx={{ maxWidth: 820, mx: "auto" }} dir="rtl">
            {!embedded && <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>تنظیمات انبار</Typography>}
            {embedded && <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>تنظیمات انبار</Typography>}
            <Stack spacing={2}>
                <Paper variant="outlined" sx={{ p: 3, borderRadius: 3 }}>
                    <Typography sx={{ fontWeight: 700, mb: 1 }}>اتصال سفارش‌ها به انبار</Typography>
                    <Typography sx={{ color: "text.secondary", mb: 2 }}>
                        با فعال‌بودن انبارداری، تأیید سفارش بر اساس رسپی، انبار پیش‌فرض و موجودی کالا انجام می‌شود.
                        در حالت غیرفعال، سفارش‌ها بدون ثبت رزرو و مصرف موجودی مدیریت می‌شوند.
                    </Typography>
                    {loading ? <CircularProgress size={24} /> : (
                        <FormControlLabel control={<Switch checked={enabled} onChange={handleChange} disabled={saving} />}
                            label={enabled ? "انبارداری فعال است" : "فقط مدیریت سفارش فعال است"} />
                    )}
                    {saving && <Typography variant="caption" sx={{ display: "block" }}>در حال ذخیره…</Typography>}
                    {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
                    <Alert severity="info" sx={{ mt: 2 }}>
                        غیرفعال‌کردن این گزینه، سوابق و رزروهای سفارش‌هایی را که قبلاً با انبارداری تأیید شده‌اند حذف نمی‌کند.
                    </Alert>
                </Paper>
                <Paper variant="outlined" sx={{ p: 3, borderRadius: 3 }}>
                    <Stack
                        direction={{ xs: "column", sm: "row" }}
                        spacing={2}
                        sx={{ alignItems: { sm: "center" }, justifyContent: "space-between" }}
                    >
                        <Box>
                            <Typography sx={{ fontWeight: 700 }}>مدیریت انبارها</Typography>
                            <Typography variant="body2" color="text.secondary">ایجاد، ویرایش و تعیین انبار پیش‌فرض کسب‌وکار</Typography>
                        </Box>
                        <Button variant="outlined" onClick={() => setWarehousesOpen(true)}>مدیریت انبارها</Button>
                    </Stack>
                </Paper>
            </Stack>
            <Dialog open={warehousesOpen} onClose={() => setWarehousesOpen(false)} fullWidth maxWidth="lg" scroll="paper">
                <DialogTitle sx={{ fontWeight: 700 }}>مدیریت انبارها</DialogTitle>
                <DialogContent dividers><WarehousesPage embedded /></DialogContent>
            </Dialog>
        </Box>
    );
};
