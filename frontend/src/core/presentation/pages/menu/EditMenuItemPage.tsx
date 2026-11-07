import {useEffect, useMemo, useState, type FormEvent} from "react";
import {useNavigate, useParams} from "react-router-dom";
import {
    Alert, Box, Button, Checkbox, CircularProgress, Container, FormControlLabel,
    Paper, Stack, TextField, Typography,
} from "@mui/material";
import {useGetMenus} from "../../hooks/menu/useGetMenus.ts";
import {useUpdateMenuItem} from "../../hooks/menu/useUpdateMenuItem.ts";
import type {MenuItem} from "../../../domain/entities/product/menu/MenuItem.ts";

interface FormState {
    name: string;
    description: string;
    price: string;
    imageUrl: string;
    recipeId: string;
    isAvailable: boolean;
}

const emptyForm: FormState = {
    name: "",
    description: "",
    price: "",
    imageUrl: "",
    recipeId: "",
    isAvailable: true,
};

export const EditMenuItemPage = () => {
    const {id} = useParams();
    const itemId = Number(id);
    const navigate = useNavigate();
    const {data: menus = [], isLoading, isError} = useGetMenus();
    const {mutate: updateItem, isPending, isError: isSaveError} = useUpdateMenuItem();
    const [form, setForm] = useState<FormState>(emptyForm);

    const item = useMemo<MenuItem | undefined>(
        () => menus.flatMap((menu) => menu.items).find((candidate) => candidate.id === itemId),
        [menus, itemId],
    );

    useEffect(() => {
        if (!item) return;
        setForm({
            name: item.name,
            description: item.description ?? "",
            price: String(item.price),
            imageUrl: item.imageUrl ?? "",
            recipeId: item.recipeId ?? "",
            isAvailable: item.isAvailable ?? true,
        });
    }, [item]);

    const change = (field: keyof FormState, value: string | boolean) => {
        setForm((current) => ({...current, [field]: value}));
    };

    const submit = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!item || item.id == null) return;
        const price = Number(form.price);
        if (!Number.isFinite(price) || price <= 0) return;

        updateItem({
            id: item.id,
            input: {
                name: form.name.trim(),
                description: form.description.trim() || null,
                price,
                imageUrl: form.imageUrl.trim() || null,
                recipeId: form.recipeId.trim() || null,
                isAvailable: form.isAvailable,
            },
        }, {onSuccess: () => navigate("/menus")});
    };

    if (!id || !Number.isInteger(itemId) || itemId <= 0) {
        return <Container maxWidth="md" sx={{py: 4}}><Alert severity="error">شناسه آیتم معتبر نیست.</Alert></Container>;
    }
    if (isLoading) return <Box sx={{display: "flex", justifyContent: "center", py: 8}}><CircularProgress /></Box>;
    if (isError) return <Container maxWidth="md" sx={{py: 4}}><Alert severity="error">دریافت اطلاعات منوها ناموفق بود.</Alert></Container>;
    if (!item) return <Container maxWidth="md" sx={{py: 4}}><Alert severity="warning">آیتم منو پیدا نشد یا به کسب‌وکار فعلی تعلق ندارد.</Alert><Button sx={{mt: 2}} onClick={() => navigate("/menus")}>بازگشت به منوها</Button></Container>;

    return (
        <Container maxWidth="md" sx={{py: 4}} dir="rtl">
            <Paper component="form" onSubmit={submit} sx={{p: {xs: 2, sm: 4}}}>
                <Stack spacing={2.5}>
                    <Box>
                        <Typography variant="h5" sx={{fontWeight: 700}}>ویرایش آیتم منو</Typography>
                        <Typography color="text.secondary">تغییرات فقط روی همین آیتم ذخیره می‌شود و سایر آیتم‌های منو دست‌نخورده می‌مانند.</Typography>
                    </Box>
                    <TextField label="نام آیتم" required slotProps={{htmlInput: {maxLength: 120}}} value={form.name} onChange={(e) => change("name", e.target.value)} />
                    <TextField label="توضیحات" multiline minRows={3} value={form.description} onChange={(e) => change("description", e.target.value)} />
                    <TextField label="قیمت (تومان)" type="number" required slotProps={{htmlInput: {min: 0.01, step: "0.01"}}} value={form.price} onChange={(e) => change("price", e.target.value)} />
                    <TextField label="آدرس تصویر" value={form.imageUrl} onChange={(e) => change("imageUrl", e.target.value)} />
                    <TextField label="شناسه رسپی (اختیاری)" type="number" value={form.recipeId} onChange={(e) => change("recipeId", e.target.value)} helperText="در صورت اتصال رسپی، شناسه رسپی متعلق به همین کسب‌وکار را وارد کنید." />
                    <FormControlLabel control={<Checkbox checked={form.isAvailable} onChange={(e) => change("isAvailable", e.target.checked)} />} label="این آیتم برای سفارش در دسترس است" />
                    {isSaveError && <Alert severity="error">ذخیره تغییرات ناموفق بود. اطلاعات و دسترسی خود را بررسی کنید.</Alert>}
                    <Stack direction="row" spacing={1}>
                        <Button type="submit" variant="contained" disabled={isPending || !form.name.trim() || !form.price || Number(form.price) <= 0}>{isPending ? "در حال ذخیره..." : "ذخیره تغییرات"}</Button>
                        <Button variant="outlined" onClick={() => navigate("/menus")} disabled={isPending}>انصراف</Button>
                    </Stack>
                </Stack>
            </Paper>
        </Container>
    );
};
