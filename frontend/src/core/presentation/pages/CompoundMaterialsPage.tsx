import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Box, Button, Chip, CircularProgress, Container, MenuItem, Pagination, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from "@mui/material";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import { apiClient } from "../../data/http/http-client";
import { useAuthStore } from "../store/auth.store";

type ComponentLine = { id?: number; ingredient_id: number; ingredient_name?: string; material_type?: "raw"; quantity: string; unit: string };
type CompoundMaterial = { id: number; name: string; sku: string | null; unit: string; material_type: "compound"; is_active: boolean; components: ComponentLine[] };
type Page<T> = { count: number; page: number; page_size: number; results: T[] };
type InventoryItem = { id: number; name: string; unit: string; preparation_level: "raw" | "semi_prepared"; is_active: boolean };
const labels: Record<string, string> = { kg: "کیلوگرم", g: "گرم", l: "لیتر", ml: "میلی‌لیتر", pc: "عدد", pk: "بسته" };
const compatible = (unit: string) => unit === "kg" || unit === "g" ? ["kg", "g"] : unit === "l" || unit === "ml" ? ["l", "ml"] : [unit];
const errorText = (error: unknown) => {
    const data = (error as { response?: { data?: unknown } })?.response?.data;
    const flatten = (value: unknown): string[] => typeof value === "string" ? [value] : Array.isArray(value) ? value.flatMap(flatten) : value && typeof value === "object" ? Object.values(value as Record<string, unknown>).flatMap(flatten) : [];
    const messages = flatten(data);
    return messages.length ? messages.join("، ") : error instanceof Error ? error.message : "درخواست ناموفق بود. دوباره تلاش کنید.";
};

const invalidateCompoundMaterialQueries = async (client: ReturnType<typeof useQueryClient>) => {
    await Promise.all([
        client.invalidateQueries({ queryKey: ["compound-materials"] }),
        client.invalidateQueries({ queryKey: ["compound-material"] }),
        client.invalidateQueries({ queryKey: ["compound-eligible-ingredients"] }),
        client.invalidateQueries({ queryKey: ["inventory-opening-items"] }),
        client.invalidateQueries({ queryKey: ["inventory-operation-items"] }),
        client.invalidateQueries({ queryKey: ["recipe-inventory-items"] }),
        client.invalidateQueries({ queryKey: ["recipes"] }),
        client.invalidateQueries({ queryKey: ["recipe"] }),
        client.invalidateQueries({ queryKey: ["inventory-stock-balances"] }),
        client.invalidateQueries({ queryKey: ["inventory-movement-history"] }),
        client.invalidateQueries({ queryKey: ["inventory-operations"] }),
        client.invalidateQueries({ queryKey: ["inventory-opening-document"] }),
    ]);
};

export const CompoundMaterialsPage = () => {
    const me = useAuthStore((state) => state.me);
    const permissions = me?.active_business?.permissions ?? [];
    const canView = permissions.includes("inventory.view");
    const canManage = permissions.includes("inventory.compound.manage");
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState("");
    const [active, setActive] = useState("all");
    const queryClient = useQueryClient();
    const query = useQuery({
        queryKey: ["compound-materials", me?.id ?? null, me?.active_business?.id ?? null, page, search, active], enabled: canView,
        queryFn: async () => (await apiClient.get<Page<CompoundMaterial>>("/inventory/compound-materials/", { params: { page, page_size: 20, ...(search ? { search } : {}), ...(active !== "all" ? { is_active: active === "active" } : {}) } })).data,
    });
    const toggle = useMutation({
        mutationFn: async ({ id, is_active }: { id: number; is_active: boolean }) => apiClient.patch(`/inventory/compound-materials/${id}/`, { is_active }),
        onSuccess: () => invalidateCompoundMaterialQueries(queryClient),
    });
    const text = query.error ? errorText(query.error) : toggle.error ? errorText(toggle.error) : "";
    return <Container maxWidth="xl" sx={{ py: 2, pb: canManage ? 12 : 2 }} dir="rtl">
        <Stack spacing={2.5}>
            <Box><Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>مواد مرکب</Typography><Typography color="text.secondary" sx={{ mt: .5 }}>تعریف مواد نیمه‌آماده و ترکیب آن‌ها از مواد اولیه؛ تعریف ترکیب موجودی را مصرف نمی‌کند.</Typography></Box>
            {!canView && <Alert severity="error">اجازه مشاهده مواد مرکب را ندارید.</Alert>}
            {!!text && <Alert severity="error" action={query.isError ? <Button color="inherit" onClick={() => void query.refetch()}>تلاش دوباره</Button> : undefined}>{text}</Alert>}
            <Paper component="form" onSubmit={(event) => { event.preventDefault(); setPage(1); }} elevation={0} sx={{ p: 2, border: 1, borderColor: "divider", borderRadius: 1 }}>
                <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                    <TextField label="جستجوی نام یا کد" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} size="small" fullWidth />
                    <TextField select label="وضعیت" value={active} onChange={(event) => { setActive(event.target.value); setPage(1); }} size="small" sx={{ minWidth: 170 }}><MenuItem value="all">همه</MenuItem><MenuItem value="active">فعال</MenuItem><MenuItem value="inactive">غیرفعال</MenuItem></TextField>
                </Stack>
            </Paper>
            {query.isLoading && <Box role="status" sx={{ display: "flex", justifyContent: "center", py: 5 }}><CircularProgress /></Box>}
            {!query.isLoading && query.data?.results.length === 0 && <Alert severity="info">ماده مرکبی برای این فیلتر پیدا نشد.</Alert>}
            {!!query.data?.results.length && <>
                <Paper elevation={0} sx={{ border: 1, borderColor: "divider", borderRadius: 3, overflow: "auto" }}><Table aria-label="فهرست مواد مرکب" sx={{ minWidth: 760 }}><TableHead><TableRow><TableCell>نام</TableCell><TableCell>کد</TableCell><TableCell>واحد خروجی</TableCell><TableCell>ترکیب</TableCell><TableCell>وضعیت</TableCell>{canManage && <TableCell>عملیات</TableCell>}</TableRow></TableHead><TableBody>{query.data.results.map((item) => <TableRow key={item.id} hover><TableCell>{item.name}</TableCell><TableCell dir="ltr">{item.sku || "—"}</TableCell><TableCell>{labels[item.unit] ?? item.unit}</TableCell><TableCell>{item.components.length ? item.components.map((line) => `${line.ingredient_name}: ${line.quantity} ${labels[line.unit] ?? line.unit}`).join("، ") : <Chip size="small" color="warning" label="ترکیب تعریف نشده" />}</TableCell><TableCell><Chip size="small" label={item.is_active ? "فعال" : "غیرفعال"} color={item.is_active ? "success" : "default"} /></TableCell>{canManage && <TableCell><Stack direction="row"><Button component={Link} to={`/materials/${item.id}/edit`} size="small" startIcon={<EditOutlinedIcon />}>ویرایش</Button><Button size="small" color={item.is_active ? "warning" : "success"} disabled={toggle.isPending} onClick={() => toggle.mutate({ id: item.id, is_active: !item.is_active })}>{item.is_active ? "غیرفعال‌سازی" : "فعال‌سازی"}</Button></Stack></TableCell>}</TableRow>)}</TableBody></Table></Paper>
                <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}><Typography color="text.secondary">تعداد کل: {query.data.count}</Typography><Pagination page={page} count={Math.max(1, Math.ceil(query.data.count / 20))} onChange={(_event, value) => setPage(value)} /></Stack>
            </>}
            {canManage && <Button component={Link} to="/materials/create" variant="contained" startIcon={<AddRoundedIcon />} aria-label="ایجاد ماده مرکب" sx={{ position: "fixed", bottom: { xs: 20, md: 32 }, left: { xs: 20, md: 32 }, zIndex: (theme) => theme.zIndex.speedDial }}>ماده مرکب جدید</Button>}
        </Stack>
    </Container>;
};

export const CompoundMaterialFormPage = () => {
    const { id } = useParams();
    return <CompoundMaterialEditor key={id ?? "new"} id={id} />;
};

const CompoundMaterialEditor = ({ id }: { id?: string }) => {
    const navigate = useNavigate();
    const client = useQueryClient();
    const me = useAuthStore((state) => state.me);
    const permissions = me?.active_business?.permissions ?? [];
    const canView = permissions.includes("inventory.view");
    const canManage = permissions.includes("inventory.compound.manage");
    const [name, setName] = useState("");
    const [sku, setSku] = useState("");
    const [unit, setUnit] = useState("kg");
    const [isActive, setIsActive] = useState(true);
    const [ingredientId, setIngredientId] = useState("");
    const [quantity, setQuantity] = useState("");
    const [componentUnit, setComponentUnit] = useState("");
    const [components, setComponents] = useState<ComponentLine[]>([]);
    const [lineError, setLineError] = useState("");
    const initialized = useRef(false);
    const existing = useQuery({ queryKey: ["compound-material", me?.id ?? null, me?.active_business?.id ?? null, id], enabled: canView && Boolean(id), queryFn: async () => (await apiClient.get<CompoundMaterial>(`/inventory/compound-materials/${id}/`)).data });
    const items = useQuery({ queryKey: ["compound-eligible-ingredients", me?.id ?? null, me?.active_business?.id ?? null], enabled: canView, queryFn: async () => {
        const size = 100;
        const first = (await apiClient.get<Page<InventoryItem>>("/inventory/items/", { params: { page: 1, page_size: size, is_active: true, preparation_level: "raw" } })).data;
        const results = [...first.results];
        for (let page = 2; page <= Math.ceil(first.count / size); page += 1) {
            const next = (await apiClient.get<Page<InventoryItem>>("/inventory/items/", { params: { page, page_size: size, is_active: true, preparation_level: "raw" } })).data;
            results.push(...next.results);
            if (next.results.length < size) break;
        }
        return results;
    } });
    useEffect(() => {
        if (!existing.data || initialized.current) return;
        initialized.current = true;
        setName(existing.data.name); setSku(existing.data.sku ?? ""); setUnit(existing.data.unit);
        setIsActive(existing.data.is_active); setComponents(existing.data.components);
    }, [existing.data]);
    const save = useMutation({
        mutationFn: async () => {
            if (!name.trim()) throw new Error("نام ماده مرکب را وارد کنید.");
            if (components.length < 2) throw new Error("حداقل دو ماده اولیه به ترکیب اضافه کنید.");
            if (components.some((line) => !/^(?:\d+(?:\.\d{1,12})?|\.\d{1,12})$/.test(line.quantity) || !/[1-9]/.test(line.quantity))) throw new Error("مقدار هر جزء باید مثبت و حداکثر با ۱۲ رقم اعشار باشد.");
            const payload = { name: name.trim(), sku: sku.trim() || null, unit, is_active: isActive, components: components.map(({ ingredient_id, quantity: amount, unit: lineUnit }) => ({ ingredient_id, quantity: amount, unit: lineUnit })) };
            return id ? apiClient.patch(`/inventory/compound-materials/${id}/`, payload) : apiClient.post("/inventory/compound-materials/", payload);
        },
        onSuccess: async () => { await invalidateCompoundMaterialQueries(client); navigate("/materials"); },
    });
    const add = () => {
        const selected = items.data?.find((item) => item.id === Number(ingredientId));
        if (!selected) { setLineError("یک ماده اولیه فعال انتخاب کنید."); return; }
        const [integer = "", fraction = ""] = quantity.split(".");
        const validQuantity = /^(?:\d+(?:\.\d{1,12})?|\.\d{1,12})$/.test(quantity)
            && integer.replace(/^0+/, "").length <= 24 && fraction.length <= 12 && /[1-9]/.test(quantity);
        if (!validQuantity) { setLineError("مقدار باید مثبت و با حداکثر ۲۴ رقم صحیح و ۱۲ رقم اعشار باشد."); return; }
        if (components.some((line) => line.ingredient_id === selected.id)) { setLineError("هر ماده اولیه فقط یک‌بار در ترکیب مجاز است."); return; }
        setComponents((current) => [...current, { ingredient_id: selected.id, ingredient_name: selected.name, material_type: "raw", quantity, unit: componentUnit || selected.unit }]);
        setIngredientId(""); setQuantity(""); setComponentUnit("");
        setLineError("");
    };
    const currentError = existing.error ?? items.error ?? save.error;
    return <Container maxWidth="md" sx={{ py: 2 }} dir="rtl"><Stack spacing={2.5}>
        <Box><Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>{id ? "ویرایش ماده مرکب" : "ماده مرکب جدید"}</Typography><Typography color="text.secondary">تعریف ترکیب، موجودی مواد اولیه را تغییر نمی‌دهد.</Typography></Box>
        {!canView && <Alert severity="error">اجازه مشاهده مواد مرکب را ندارید.</Alert>}{canView && !canManage && <Alert severity="warning">برای تغییر مواد مرکب به مجوز مدیریت مواد مرکب نیاز دارید.</Alert>}
        {(existing.isLoading || items.isLoading) && <Box role="status" sx={{ display: "flex", justifyContent: "center", py: 4 }}><CircularProgress /></Box>}
        {currentError && <Alert severity="error">{errorText(currentError)}</Alert>}
        {canManage && !existing.isLoading && !items.isLoading && !currentError && <Paper component="form" onSubmit={(event) => { event.preventDefault(); save.mutate(); }} elevation={0} sx={{ p: 2.5, border: 1, borderColor: "divider", borderRadius: 3 }}><Stack spacing={2}>
            <TextField required label="نام ماده مرکب" value={name} onChange={(event) => setName(event.target.value)} slotProps={{ htmlInput: { maxLength: 120 } }} />
            <TextField label="کد (SKU)" value={sku} onChange={(event) => setSku(event.target.value)} slotProps={{ htmlInput: { maxLength: 50 } }} />
            <TextField select label="واحد ماده مرکب" value={unit} onChange={(event) => setUnit(event.target.value)}>{["kg", "g", "l", "ml", "pc", "pk"].map((entry) => <MenuItem key={entry} value={entry}>{labels[entry]}</MenuItem>)}</TextField>
            {id && <TextField select label="وضعیت" value={isActive ? "active" : "inactive"} onChange={(event) => setIsActive(event.target.value === "active")}><MenuItem value="active">فعال</MenuItem><MenuItem value="inactive">غیرفعال</MenuItem></TextField>}
            <Typography variant="h6">ترکیب مواد اولیه</Typography>
            {lineError && <Alert severity="error">{lineError}</Alert>}
            <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
                <TextField select label="ماده اولیه" value={ingredientId} onChange={(event) => { setIngredientId(event.target.value); setComponentUnit(""); }} fullWidth>{(items.data ?? []).filter((item) => !components.some((line) => line.ingredient_id === item.id)).map((item) => <MenuItem key={item.id} value={item.id}>{item.name} · {labels[item.unit] ?? item.unit}</MenuItem>)}</TextField>
                <TextField label="مقدار" value={quantity} onChange={(event) => setQuantity(event.target.value)} slotProps={{ htmlInput: { inputMode: "decimal" } }} />
                <TextField select label="واحد" value={componentUnit || (items.data ?? []).find((item) => item.id === Number(ingredientId))?.unit || ""} onChange={(event) => setComponentUnit(event.target.value)} disabled={!ingredientId}>{ingredientId && compatible((items.data ?? []).find((item) => item.id === Number(ingredientId))?.unit ?? "").map((entry) => <MenuItem key={entry} value={entry}>{labels[entry] ?? entry}</MenuItem>)}</TextField>
                <Button type="button" variant="outlined" onClick={add} disabled={!ingredientId}>افزودن</Button>
            </Stack>
            {components.map((line) => {
                const ingredient = items.data?.find((item) => item.id === line.ingredient_id);
                return <Paper variant="outlined" key={line.ingredient_id} sx={{ p: 1.5 }}><Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ alignItems: { sm: "center" } }}>
                    <Typography sx={{ flex: 1 }}>{line.ingredient_name}</Typography>
                    <TextField label="مقدار" value={line.quantity} onChange={(event) => setComponents((current) => current.map((entry) => entry.ingredient_id === line.ingredient_id ? { ...entry, quantity: event.target.value } : entry))} slotProps={{ htmlInput: { inputMode: "decimal" } }} size="small" />
                    <TextField select label="واحد" value={line.unit} onChange={(event) => setComponents((current) => current.map((entry) => entry.ingredient_id === line.ingredient_id ? { ...entry, unit: event.target.value } : entry))} size="small" sx={{ minWidth: 140 }}>{compatible(ingredient?.unit ?? line.unit).map((entry) => <MenuItem key={entry} value={entry}>{labels[entry] ?? entry}</MenuItem>)}</TextField>
                    <Button color="error" onClick={() => setComponents((current) => current.filter((entry) => entry.ingredient_id !== line.ingredient_id))}>حذف</Button>
                </Stack></Paper>;
            })}
            <Typography variant="caption" color="text.secondary">حداقل دو ماده اولیهٔ فعال از همین کسب‌وکار لازم است. مقدارها با واحد سازگار ثبت می‌شوند.</Typography>
            <Stack direction="row" spacing={1}><Button type="button" onClick={() => navigate("/materials")}>بازگشت</Button><Button type="submit" variant="contained" disabled={save.isPending}>{save.isPending ? "در حال ذخیره…" : "ذخیره"}</Button></Stack>
        </Stack></Paper>}
    </Stack></Container>;
};
