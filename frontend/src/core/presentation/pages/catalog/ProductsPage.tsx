import { useDeferredValue, useEffect, useState } from "react";
import {
    Alert, Box, Button, Chip, CircularProgress, Dialog, DialogActions, DialogContent,
    DialogTitle, IconButton, MenuItem, Paper, Table, TableBody, TableCell,
    TableContainer, TableHead, TableRow, TextField, Typography,
} from "@mui/material";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import EditRoundedIcon from "@mui/icons-material/EditRounded";
import Inventory2RoundedIcon from "@mui/icons-material/Inventory2Rounded";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import { useCreateProduct, useProducts, useUpdateProduct } from "../../hooks/catalog/useProducts.ts";
import type { Product, ProductInput, ProductStatus } from "../../../domain/entities/catalog/Product.ts";

const emptyForm: ProductInput = { name: "", sku: "", category: "", description: "", status: "draft" };

const statusLabels: Record<ProductStatus, string> = {
    draft: "پیش‌نویس",
    active: "فعال",
    archived: "بایگانی‌شده",
};

export const ProductsPage = () => {
    const [search, setSearch] = useState("");
    const deferredSearch = useDeferredValue(search);
    const { data, isLoading, isError, error } = useProducts(deferredSearch);
    const createProduct = useCreateProduct();
    const updateProduct = useUpdateProduct();
    const [dialogOpen, setDialogOpen] = useState(false);
    const [editing, setEditing] = useState<Product | null>(null);
    const [form, setForm] = useState<ProductInput>(emptyForm);
    const [formError, setFormError] = useState("");

    useEffect(() => {
        if (!dialogOpen) {
            setEditing(null);
            setForm(emptyForm);
            setFormError("");
        }
    }, [dialogOpen]);

    const openCreate = () => {
        setEditing(null);
        setForm(emptyForm);
        setFormError("");
        setDialogOpen(true);
    };

    const openEdit = (product: Product) => {
        setEditing(product);
        setForm({
            name: product.name,
            sku: product.sku ?? "",
            category: product.category ?? "",
            description: product.description ?? "",
            status: product.status,
        });
        setFormError("");
        setDialogOpen(true);
    };

    const save = async () => {
        if (!form.name?.trim()) {
            setFormError("نام محصول الزامی است.");
            return;
        }
        const payload: ProductInput = {
            ...form,
            name: form.name.trim(),
            sku: form.sku?.trim() || null,
            category: form.category?.trim() || null,
            description: form.description?.trim() || null,
        };
        try {
            if (editing) await updateProduct.mutateAsync({ id: editing.id, input: payload });
            else await createProduct.mutateAsync(payload);
            setDialogOpen(false);
        } catch {
            setFormError("ذخیره محصول انجام نشد. کد کالا را بررسی کنید یا دوباره تلاش کنید.");
        }
    };

    const archive = async (product: Product) => {
        try {
            await updateProduct.mutateAsync({ id: product.id, input: { status: "archived" } });
        } catch {
            setFormError("بایگانی محصول انجام نشد. دوباره تلاش کنید.");
        }
    };

    const saving = createProduct.isPending || updateProduct.isPending;

    return (
        <Box sx={{ p: { xs: 2, md: 3 }, minHeight: "100%", bgcolor: "#F8FAFC" }}>
            <Box sx={{ display: "flex", flexDirection: { xs: "column", sm: "row" }, justifyContent: "space-between", alignItems: { xs: "stretch", sm: "center" }, gap: 2, mb: 3 }}>
                <Box>
                    <Typography variant="h4" sx={{ fontWeight: 800 }}>کاتالوگ محصولات</Typography>
                    <Typography color="text.secondary" sx={{ mt: 0.5 }}>مدیریت هویت محصولات مستقل از قیمت‌گذاری منو و موجودی انبار</Typography>
                </Box>
                <Button variant="contained" startIcon={<AddRoundedIcon />} onClick={openCreate}>محصول جدید</Button>
            </Box>

            <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                <TextField
                    fullWidth
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="جستجو بر اساس نام یا کد کالا"
                    slotProps={{ input: { startAdornment: <SearchRoundedIcon sx={{ mr: 1, color: "text.secondary" }} /> } }}
                />
            </Paper>

            {isError && <Alert severity="error" sx={{ mb: 2 }}>{error instanceof Error ? error.message : "دریافت محصولات با خطا مواجه شد."}</Alert>}
            {formError && !dialogOpen && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setFormError("")}>{formError}</Alert>}

            <Paper variant="outlined" sx={{ overflow: "hidden" }}>
                {isLoading ? (
                    <Box sx={{ display: "flex", justifyContent: "center", p: 6 }}><CircularProgress /></Box>
                ) : data?.results.length ? (
                    <TableContainer>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>محصول</TableCell>
                                    <TableCell>کد کالا (SKU)</TableCell>
                                    <TableCell>دسته‌بندی</TableCell>
                                    <TableCell>وضعیت</TableCell>
                                    <TableCell align="right">عملیات</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {data.results.map((product: Product) => (
                                    <TableRow key={product.id} hover>
                                        <TableCell>
                                            <Box sx={{ display: "flex", flexDirection: "row", gap: 1.5, alignItems: "center" }}>
                                                <Box sx={{ width: 38, height: 38, borderRadius: 1, bgcolor: "action.hover", display: "grid", placeItems: "center" }}>
                                                    <Inventory2RoundedIcon color="action" />
                                                </Box>
                                                <Box>
                                                    <Typography sx={{ fontWeight: 700 }}>{product.name}</Typography>
                                                    {product.description && <Typography variant="caption" color="text.secondary">{product.description}</Typography>}
                                                </Box>
                                            </Box>
                                        </TableCell>
                                        <TableCell>{product.sku || "—"}</TableCell>
                                        <TableCell>{product.category || "—"}</TableCell>
                                        <TableCell>
                                            <Chip size="small" label={statusLabels[product.status]} color={product.status === "active" ? "success" : product.status === "archived" ? "default" : "warning"} />
                                        </TableCell>
                                        <TableCell align="right">
                                            <IconButton aria-label="ویرایش محصول" onClick={() => openEdit(product)}><EditRoundedIcon /></IconButton>
                                            {product.status !== "archived" && <Button size="small" color="inherit" onClick={() => archive(product)}>بایگانی</Button>}
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                ) : (
                    <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 1, py: 7, px: 2 }}>
                        <Inventory2RoundedIcon sx={{ fontSize: 44, color: "text.disabled" }} />
                        <Typography sx={{ fontWeight: 700 }}>{search ? "محصولی با این عبارت پیدا نشد" : "هنوز محصولی ثبت نشده است"}</Typography>
                        <Typography variant="body2" color="text.secondary">برای شروع، اولین محصول کسب‌وکارت را ثبت کن.</Typography>
                        {!search && <Button onClick={openCreate} startIcon={<AddRoundedIcon />}>ثبت محصول</Button>}
                    </Box>
                )}
            </Paper>

            <Box sx={{ display: "flex", flexDirection: "row", justifyContent: "space-between", mt: 1.5 }}>
                <Typography variant="caption" color="text.secondary">تعداد کل: {data?.count ?? 0}</Typography>
                <Typography variant="caption" color="text.secondary">نمایش {data?.results.length ?? 0} مورد از هر صفحه</Typography>
            </Box>

            <Dialog open={dialogOpen} onClose={() => !saving && setDialogOpen(false)} fullWidth maxWidth="sm">
                <DialogTitle>{editing ? "ویرایش محصول" : "ثبت محصول جدید"}</DialogTitle>
                <DialogContent>
                    <Box sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
                        {formError && <Alert severity="error">{formError}</Alert>}
                        <TextField label="نام محصول" required autoFocus value={form.name ?? ""} onChange={(e) => setForm((old) => ({ ...old, name: e.target.value }))} />
                        <TextField label="کد کالا (SKU)" value={form.sku ?? ""} onChange={(e) => setForm((old) => ({ ...old, sku: e.target.value }))} />
                        <TextField label="دسته‌بندی" value={form.category ?? ""} onChange={(e) => setForm((old) => ({ ...old, category: e.target.value }))} />
                        <TextField label="توضیحات" multiline minRows={3} value={form.description ?? ""} onChange={(e) => setForm((old) => ({ ...old, description: e.target.value }))} />
                        <TextField select label="وضعیت" value={form.status ?? "draft"} onChange={(e) => setForm((old) => ({ ...old, status: e.target.value as ProductStatus }))}>
                            <MenuItem value="draft">پیش‌نویس</MenuItem>
                            <MenuItem value="active">فعال</MenuItem>
                            <MenuItem value="archived">بایگانی‌شده</MenuItem>
                        </TextField>
                    </Box>
                </DialogContent>
                <DialogActions sx={{ p: 2 }}>
                    <Button onClick={() => setDialogOpen(false)} disabled={saving}>انصراف</Button>
                    <Button variant="contained" onClick={save} disabled={saving}>{saving ? "در حال ذخیره..." : "ذخیره"}</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};
