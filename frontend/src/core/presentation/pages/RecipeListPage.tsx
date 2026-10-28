import { useState } from "react";
import { Link } from "react-router-dom";
import {
    Alert, Box, Button, CircularProgress, Container, Paper, Stack,
    Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography,
} from "@mui/material";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import { useGetAllRecipes } from "../hooks/useGetAllRecipes";
import { useAuthStore } from "../store/auth.store";

export const RecipeListPage = () => {
    const [search, setSearch] = useState("");
    const permissions = useAuthStore((state) => state.me?.active_business?.permissions ?? []);
    const canManageRecipes = permissions.includes("inventory.recipe.manage");
    const { data = [], isLoading, isError } = useGetAllRecipes({ search: search.trim() || undefined });

    return (
        <Container maxWidth="xl" sx={{ py: 2 }} dir="rtl">
            <Stack spacing={2.5}>
                <Stack direction={{ xs: "column", sm: "row" }} sx={{ justifyContent: "space-between", alignItems: { sm: "center" }, gap: 2 }}>
                    <Box>
                        <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>رسپی‌ها</Typography>
                        <Typography color="text.secondary">تعریف مواد اولیه و مقدار مصرف هر دستور</Typography>
                    </Box>
                    {canManageRecipes && <Button component={Link} to="/recipes/create" variant="contained">رسپی جدید</Button>}
                </Stack>
                <Paper sx={{ p: 2 }}>
                    <TextField
                        label="جستجوی نام یا کد رسپی"
                        value={search}
                        onChange={(event) => setSearch(event.target.value)}
                        size="small"
                        fullWidth
                    />
                </Paper>
                {isLoading && <Box role="status" sx={{ display: "flex", justifyContent: "center", py: 5 }}><CircularProgress /></Box>}
                {isError && <Alert severity="error">دریافت رسپی‌ها ناموفق بود. دسترسی و اتصال را بررسی و دوباره تلاش کنید.</Alert>}
                {!isLoading && !isError && data.length === 0 && <Alert severity="info">رسپی‌ای برای این فیلتر پیدا نشد.</Alert>}
                {!isLoading && !isError && data.length > 0 && (
                    <Paper sx={{ overflowX: "auto" }}>
                        <Table aria-label="فهرست رسپی‌ها">
                            <TableHead><TableRow><TableCell>نام</TableCell><TableCell>مواد مصرفی</TableCell><TableCell>محصولات خروجی</TableCell><TableCell>توضیحات</TableCell>{canManageRecipes && <TableCell>عملیات</TableCell>}</TableRow></TableHead>
                            <TableBody>{data.map(({ recipe, ingredients, outputs }) => (
                                <TableRow key={recipe.id} hover>
                                    <TableCell>{recipe.name}</TableCell>
                                    <TableCell>{ingredients.map((line) => `${line.ingredientName ?? "ماده"} (${line.materialType === "compound" ? "مرکب" : "اولیه"}): ${line.quantity} ${line.unit ?? ""}`).join("، ") || "—"}</TableCell>
                                    <TableCell>{outputs.map((line) => `${line.ingredientName ?? "محصول"} (${line.materialType === "compound" ? "مرکب" : "اولیه"}): ${line.quantity} ${line.unit ?? ""}${line.isPrimary ? " (اصلی)" : ""}`).join("، ") || "—"}</TableCell>
                                    <TableCell>{recipe.description || "—"}</TableCell>
                                    {canManageRecipes && <TableCell><Button component={Link} to={`/recipes/${recipe.id}/edit`} size="small" startIcon={<EditOutlinedIcon />}>ویرایش</Button></TableCell>}
                                </TableRow>
                            ))}</TableBody>
                        </Table>
                    </Paper>
                )}
            </Stack>
        </Container>
    );
};
