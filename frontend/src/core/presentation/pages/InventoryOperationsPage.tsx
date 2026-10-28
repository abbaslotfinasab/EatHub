import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
    Alert, Box, Button, Chip, CircularProgress, Dialog, DialogActions, DialogContent,
    DialogTitle, Divider, MenuItem, Paper, Stack, Tab, Tabs,
    Skeleton, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
    TextField, Typography,
} from "@mui/material";
import Inventory2RoundedIcon from "@mui/icons-material/Inventory2Rounded";
import { apiClient } from "../../data/http/http-client";
import { useAuthStore } from "../store/auth.store";

type Item = { id: number; name: string; unit: string; preparation_level: "raw" | "semi_prepared" };
type Warehouse = { id: number; name: string; is_active: boolean };
type Line = {
    id: number; ingredient_id: number; ingredient_name: string; material_type: "raw" | "compound"; quantity: string; unit: string;
    system_quantity: string | null; counted_quantity: string | null; counted_unit_cost: string | null;
    variance: string | null; in_transit_quantity: string;
};
type Operation = { id: number; status: string; type: string; warehouse_name: string; destination_warehouse_name: string | null; reference: string; reason: string; notes: string; lines: Line[] };
type Page<T> = { count: number; results: T[] };
type Movement = { id: number; type: string; direction: string; quantity: string; unit: string; balance_after: string; ingredient_name: string; material_type: "raw" | "compound"; warehouse_name: string; source_type: string; source_document_id: number; reason: string | null };
type DraftLine = { ingredient_id: number; ingredient_name: string; material_type: "raw" | "compound"; quantity: string; unit: string };
const fetchPages = async <T,>(path: string, params: Record<string, unknown>): Promise<T[]> => {
    const size = 100;
    const first = (await apiClient.get<Page<T>>(path, { params: { ...params, page: 1, page_size: size } })).data;
    const results = [...first.results];
    const pageCount = Math.ceil(first.count / size);
    for (let page = 2; page <= pageCount; page += 1) {
        const next = (await apiClient.get<Page<T>>(path, { params: { ...params, page, page_size: size } })).data;
        results.push(...next.results);
        if (next.results.length < size) break;
    }
    return results;
};

const kinds = ["issues", "transfers", "stocktakes"] as const;
type Kind = typeof kinds[number];
const titles: Record<Kind, string> = { issues: "حواله‌های خروج", transfers: "انتقال بین انبارها", stocktakes: "انبارگردانی" };
const statusLabels: Record<string, string> = { draft: "پیش‌نویس", posted: "ثبت‌شده", in_transit: "در مسیر", received: "دریافت‌شده", cancelled: "لغوشده", reversed: "برگشت‌خورده", approved: "تأییدشده" };
const movementLabels: Record<string, string> = { receipt: "دریافت", issue: "خروج", transfer_dispatch: "ارسال انتقال", transfer_receipt: "دریافت انتقال", adjustment: "تعدیل", reversal: "برگشت", opening_balance: "موجودی اولیه" };
const unitLabels: Record<string, string> = { kg: "کیلوگرم", g: "گرم", l: "لیتر", ml: "میلی‌لیتر", pc: "عدد", pk: "بسته" };

const sectionSurfaceSx = {
    border: 1,
    borderColor: "divider",
    borderRadius: 3,
    overflow: "hidden",
};

const toolbarSurfaceSx = {
    p: 2,
    border: 1,
    borderColor: "divider",
    borderRadius: 1,
    bgcolor: "background.paper",
};

const operationFieldSx = {
    flex: "1 1 190px",
    minWidth: 0,
    width: { xs: "100%", md: "auto" },
    "& .MuiOutlinedInput-root": { height: 56, borderRadius: 1 },
};

const OperationTableHead = ({ columns }: { columns: string[] }) => (
    <TableHead>
        <TableRow>
            {columns.map((column) => (
                <TableCell key={column}>
                    <Typography sx={{ fontWeight: 700 }}>{column}</Typography>
                </TableCell>
            ))}
        </TableRow>
    </TableHead>
);

const OperationStatusChip = ({ status }: { status: string }) => (
    <Chip
        label={statusLabels[status] ?? "وضعیت نامشخص"}
        size="small"
        variant="filled"
        sx={{ minWidth: 100, borderRadius: 2, fontWeight: 700 }}
        color={status === "cancelled" || status === "reversed" ? "error" : status === "draft" || status === "in_transit" ? "warning" : "success"}
    />
);

const errorMessage = (error: unknown): string => {
    const data = (error as { response?: { data?: unknown } })?.response?.data;
    if (typeof data === "string") return data;
    if (data && typeof data === "object") {
        const values = Object.values(data as Record<string, unknown>).flatMap((value) => Array.isArray(value) ? value : [value]);
        const messages = values.filter((value): value is string => typeof value === "string");
        if (messages.length) return messages.join(" ");
    }
    return error instanceof Error ? error.message : "درخواست ناموفق بود. دوباره تلاش کنید.";
};

export const InventoryOperationsPage = ({ embedded = false }: { embedded?: boolean }) => {
    const me = useAuthStore((state) => state.me);
    const permissions = me?.active_business?.permissions ?? [];
    const canView = permissions.includes("inventory.view");
    const canAdjust = permissions.includes("inventory.adjust");
    const userId = me?.id ?? null;
    const businessId = me?.active_business?.id ?? null;
    const [kind, setKind] = useState<Kind>("issues");
    const [warehouseId, setWarehouseId] = useState("");
    const [destinationId, setDestinationId] = useState("");
    const [itemId, setItemId] = useState("");
    const [materialType, setMaterialType] = useState<"raw" | "compound">("raw");
    const [quantity, setQuantity] = useState("");
    const [draftLines, setDraftLines] = useState<DraftLine[]>([]);
    const [reason, setReason] = useState("");
    const [reference, setReference] = useState("");
    const [movementType, setMovementType] = useState("");
    const [movementWarehouse, setMovementWarehouse] = useState("");
    const [movementItem, setMovementItem] = useState("");
    const [movementMaterialType, setMovementMaterialType] = useState<"" | "raw" | "compound">("");
    const [movementSearch, setMovementSearch] = useState("");
    const [movementReference, setMovementReference] = useState("");
    const [openingDocumentId, setOpeningDocumentId] = useState<number | null>(null);
    const [message, setMessage] = useState("");
    const queryClient = useQueryClient();

    const items = useQuery({ queryKey: ["inventory-operation-items", userId, businessId], enabled: canView, queryFn: () => fetchPages<Item>("/inventory/items/", { is_active: true }) });
    const warehouses = useQuery({ queryKey: ["inventory-operation-warehouses", userId, businessId], enabled: canView, queryFn: () => fetchPages<Warehouse>("/inventory/warehouses/", { is_active: true }) });
    const operations = useQuery({ queryKey: ["inventory-operations", userId, businessId, kind], enabled: canView, queryFn: async () => (await apiClient.get<Page<Operation>>(`/inventory/${kind}/`, { params: { page_size: 100 } })).data.results });
    const movements = useQuery({
        queryKey: ["inventory-movement-history", userId, businessId, movementType, movementWarehouse, movementItem, movementMaterialType, movementSearch, movementReference], enabled: canView,
        queryFn: async () => (await apiClient.get<Page<Movement>>("/inventory/movements/", { params: {
            page_size: 100, ...(movementType ? { movement_type: movementType } : {}),
            ...(movementWarehouse ? { warehouse_id: movementWarehouse } : {}),
            ...(movementItem ? { ingredient_id: movementItem } : {}), ...(movementReference ? { reference: movementReference } : {}),
            ...(movementMaterialType ? { material_type: movementMaterialType } : {}),
            ...(movementSearch.trim() ? { search: movementSearch.trim() } : {}),
        } })).data.results,
    });
    const openingDocument = useQuery({
        queryKey: ["inventory-opening-document", userId, businessId, openingDocumentId],
        enabled: canView && businessId !== null && openingDocumentId !== null,
        queryFn: async () => (await apiClient.get<Operation>(`/inventory/opening-stock/${openingDocumentId}/`)).data,
    });
    const refresh = async () => Promise.all([
        queryClient.invalidateQueries({ queryKey: ["inventory-operations"] }),
        queryClient.invalidateQueries({ queryKey: ["inventory-movement-history"] }),
    ]);
    const create = useMutation({
        mutationFn: async () => {
            if (!warehouseId) throw new Error("یک انبار را انتخاب کنید.");
            if (draftLines.length === 0) throw new Error("حداقل یک ردیف ماده اضافه کنید.");
            return (await apiClient.post(`/inventory/${kind}/`, {
                warehouse_id: Number(warehouseId), ...(kind === "transfers" ? { destination_warehouse_id: Number(destinationId) } : {}),
                reference, reason, lines: draftLines.map(({ ingredient_id, material_type, quantity: lineQuantity, unit }) => ({ ingredient_id, material_type, quantity: lineQuantity, unit })),
            })).data as Operation;
        },
        onSuccess: async () => { setMessage("پیش‌نویس ایجاد شد."); setQuantity(""); setReason(""); setReference(""); setDraftLines([]); await refresh(); },
        onError: (error: unknown) => setMessage(errorMessage(error)),
    });
    const act = useMutation({
        mutationFn: async ({ id, action }: { id: number; action: string }) => (await apiClient.post(`/inventory/${kind}/${id}/${action}/`, {})).data as Operation,
        onSuccess: refresh, onError: (error: unknown) => setMessage(errorMessage(error)),
    });
    const count = useMutation({
        mutationFn: async ({ id, line, value, unitCost }: { id: number; line: Line; value: string; unitCost?: string }) => apiClient.patch(`/inventory/stocktakes/${id}/`, { lines: [{ id: line.id, counted_quantity: value, ...(unitCost ? { counted_unit_cost: unitCost } : {}) }] }),
        onSuccess: refresh, onError: (error: unknown) => setMessage(errorMessage(error)),
    });
    const loading = items.isLoading || warehouses.isLoading || operations.isLoading;
    const error = items.error || warehouses.error || operations.error;

    return <Box dir="rtl" sx={{ width: "100%" }}>
        <Stack spacing={3}>
            {!embedded && <Box><Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>عملیات موجودی</Typography><Typography color="text.secondary">خروج، انتقال، انبارگردانی و تاریخچه گردش کالا</Typography></Box>}
            {!canView && <Alert severity="error">اجازه مشاهده موجودی را ندارید.</Alert>}
            {!!error && <Alert severity="error">بارگذاری اطلاعات ناموفق بود. دسترسی و اتصال را بررسی و دوباره تلاش کنید.</Alert>}
            {!!message && <Alert severity="info" onClose={() => setMessage("")}>{message}</Alert>}
            {canView && <>
                {canAdjust && <>
                    <Paper elevation={0} sx={sectionSurfaceSx}><Tabs value={kind} onChange={(_event, value: Kind) => setKind(value)} aria-label="عملیات انبار" variant="scrollable" allowScrollButtonsMobile sx={{ px: 1 }}>
                        {kinds.map((entry) => <Tab key={entry} value={entry} label={titles[entry]} />)}
                    </Tabs></Paper>
                    <Paper component="form" elevation={0} onSubmit={(event) => { event.preventDefault(); create.mutate(); }} sx={toolbarSurfaceSx}>
                        <Stack spacing={2}>
                            <Typography variant="h6" sx={{ fontWeight: 700 }}>ایجاد پیش‌نویس {titles[kind]}</Typography>
                            <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ flexWrap: { md: "wrap" } }}>
                                <TextField select required label="انبار مبدأ" value={warehouseId} onChange={(event) => setWarehouseId(event.target.value)} sx={operationFieldSx}>{(warehouses.data ?? []).map((row) => <MenuItem key={row.id} value={row.id}>{row.name}</MenuItem>)}</TextField>
                                {kind === "transfers" && <TextField select required label="انبار مقصد" value={destinationId} onChange={(event) => setDestinationId(event.target.value)} sx={operationFieldSx}>{(warehouses.data ?? []).filter((row) => String(row.id) !== warehouseId).map((row) => <MenuItem key={row.id} value={row.id}>{row.name}</MenuItem>)}</TextField>}
                                <TextField select label="نوع ماده" value={materialType} onChange={(event) => { setMaterialType(event.target.value as "raw" | "compound"); setItemId(""); }} sx={operationFieldSx}><MenuItem value="raw">مواد اولیه</MenuItem><MenuItem value="compound">مواد مرکب</MenuItem></TextField>
                                <TextField select required label={materialType === "raw" ? "ماده اولیه" : "ماده مرکب"} value={itemId} onChange={(event) => setItemId(event.target.value)} sx={operationFieldSx}>{(items.data ?? []).filter((row) => row.preparation_level === (materialType === "raw" ? "raw" : "semi_prepared")).map((row) => <MenuItem key={row.id} value={row.id}>{row.name} ({unitLabels[row.unit] ?? row.unit})</MenuItem>)}</TextField>
                                {kind !== "stocktakes" && <TextField required type="number" label="مقدار" value={quantity} onChange={(event) => setQuantity(event.target.value)} slotProps={{ htmlInput: { min: 0.000000000001, step: "any" } }} sx={{ ...operationFieldSx, flexBasis: 150 }} />}
                                <TextField label="شماره یا مرجع سند" value={reference} onChange={(event) => setReference(event.target.value)} sx={operationFieldSx} />
                                {kind === "issues" && <TextField required label="دلیل خروج" value={reason} onChange={(event) => setReason(event.target.value)} sx={operationFieldSx} />}
                            </Stack>
                            <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
                                <Button type="button" onClick={() => {
                                    const item = items.data?.find((entry) => entry.id === Number(itemId));
                                    if (!item || (kind !== "stocktakes" && !quantity)) { setMessage("ماده را انتخاب و مقدار مثبت وارد کنید."); return; }
                                    if (draftLines.some((line) => line.ingredient_id === item.id)) { setMessage("هر ماده فقط یک‌بار به هر سند افزوده می‌شود."); return; }
                                    setDraftLines((current) => [...current, { ingredient_id: item.id, ingredient_name: item.name, material_type: item.preparation_level === "semi_prepared" ? "compound" : "raw", quantity: kind === "stocktakes" ? "0" : quantity, unit: item.unit }]);
                                    setQuantity(""); setMessage("");
                                }} sx={{ height: 48, borderRadius: 1 }}>افزودن ماده</Button>
                                <Button type="submit" variant="contained" sx={{ height: 48, borderRadius: 1 }} disabled={create.isPending || loading || !warehouseId || draftLines.length === 0 || (kind === "transfers" && !destinationId)}>{create.isPending ? "در حال ذخیره…" : "ایجاد پیش‌نویس"}</Button>
                            </Stack>
                            {!!draftLines.length && <Paper variant="outlined" sx={{ p: 1.5, borderRadius: 2 }}><Stack divider={<Divider flexItem />}>
                                {draftLines.map((line) => <Stack key={line.ingredient_id} direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ py: 1, alignItems: { sm: "center" }, justifyContent: "space-between" }}>
                                    <Typography variant="body2">{line.ingredient_name}: {line.quantity} {unitLabels[line.unit] ?? line.unit}</Typography>
                                    <Button size="small" onClick={() => setDraftLines((current) => current.filter((entry) => entry.ingredient_id !== line.ingredient_id))}>حذف از پیش‌نویس</Button>
                                </Stack>)}
                            </Stack></Paper>}
                        </Stack>
                    </Paper>
                </>}
                {loading && <Paper elevation={0} sx={{ ...sectionSurfaceSx, p: 2 }} role="status" aria-label="در حال بارگذاری عملیات انبار"><Skeleton width="25%" height={32} />{Array.from({ length: 5 }).map((_, index) => <Skeleton key={index} height={42} />)}</Paper>}
                <Typography variant="h6" sx={{ fontWeight: 700 }}>{titles[kind]}</Typography>
                {!loading && !error && !operations.data?.length && <Paper elevation={0} sx={{ py: 6, px: 3, border: "1px dashed", borderColor: "divider", borderRadius: 3 }}><Stack spacing={2} sx={{ alignItems: "center", textAlign: "center" }}><Inventory2RoundedIcon sx={{ fontSize: 36, color: "text.secondary" }} /><Typography variant="h6" sx={{ fontWeight: 700 }}>هنوز سندی در این بخش ثبت نشده است</Typography><Typography variant="body2" color="text.secondary">با ایجاد یک پیش‌نویس، عملیات این بخش در اینجا نمایش داده می‌شود.</Typography></Stack></Paper>}
                {!!operations.data?.length && <TableContainer component={Paper} elevation={0} sx={{ ...sectionSurfaceSx, overflowX: "auto", overflowY: "hidden" }}><Table aria-label={titles[kind]} sx={{ minWidth: 850 }}><OperationTableHead columns={["شناسه و مرجع", "وضعیت", "انبارها", "مواد و جزئیات", "اقدام‌ها"]} /><TableBody>{operations.data.map((doc) => <TableRow key={doc.id} hover sx={{ "&:last-child td": { borderBottom: 0 } }}>
                    <TableCell>#{doc.id}<br />{doc.reference || "—"}</TableCell>
                    <TableCell><OperationStatusChip status={doc.status} /></TableCell>
                    <TableCell>{doc.warehouse_name}{doc.destination_warehouse_name ? ` ← ${doc.destination_warehouse_name}` : ""}</TableCell>
                    <TableCell>{doc.lines.map((line) => <Box key={line.id} sx={{ mb: 1 }}>
                        <Typography variant="body2">{line.ingredient_name} · {line.material_type === "compound" ? "مواد مرکب" : "مواد اولیه"}: {line.quantity} {unitLabels[line.unit] ?? line.unit}</Typography>
                        {line.system_quantity !== null && <Typography variant="caption" sx={{ display: "block" }}>موجودی مبنا: {line.system_quantity}</Typography>}
                        {line.counted_quantity !== null && <Typography variant="caption" sx={{ display: "block" }}>شمارش: {line.counted_quantity} · اختلاف: {line.variance}</Typography>}
                        {doc.status === "in_transit" && <Typography variant="caption" sx={{ display: "block" }}>مقدار در مسیر: {line.in_transit_quantity}</Typography>}
                        {kind === "stocktakes" && doc.status === "draft" && canAdjust && <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ mt: 1 }}>
                            <TextField size="small" type="number" label="مقدار شمارش‌شده" defaultValue={line.counted_quantity ?? ""} slotProps={{ htmlInput: { min: 0, step: "any" } }} id={`count-${doc.id}-${line.id}`} />
                            <TextField size="small" type="number" label="بهای واحد در موجودی صفر" defaultValue={line.counted_unit_cost ?? ""} slotProps={{ htmlInput: { min: 0, step: "any" } }} id={`cost-${doc.id}-${line.id}`} />
                            <Button size="small" onClick={() => { const input = document.getElementById(`count-${doc.id}-${line.id}`) as HTMLInputElement | null; const cost = document.getElementById(`cost-${doc.id}-${line.id}`) as HTMLInputElement | null; if (input?.value !== undefined) count.mutate({ id: doc.id, line, value: input.value, unitCost: cost?.value }); }}>ذخیره شمارش</Button>
                        </Stack>}
                    </Box>)}</TableCell>
                    <TableCell>{canAdjust && <Stack direction="row" sx={{ flexWrap: "wrap" }}>
                        {doc.status === "draft" && <Button size="small" onClick={() => act.mutate({ id: doc.id, action: "cancel" })}>لغو پیش‌نویس</Button>}
                        {kind === "issues" && doc.status === "draft" && <Button size="small" onClick={() => act.mutate({ id: doc.id, action: "post" })}>ثبت خروج</Button>}
                        {kind === "issues" && doc.status === "posted" && <Button size="small" onClick={() => act.mutate({ id: doc.id, action: "reverse" })}>ثبت برگشت</Button>}
                        {kind === "transfers" && doc.status === "draft" && <Button size="small" onClick={() => act.mutate({ id: doc.id, action: "dispatch" })}>ارسال از مبدأ</Button>}
                        {kind === "transfers" && doc.status === "in_transit" && <Button size="small" onClick={() => act.mutate({ id: doc.id, action: "receive" })}>دریافت کامل</Button>}
                        {kind === "stocktakes" && doc.status === "draft" && <Button size="small" onClick={() => act.mutate({ id: doc.id, action: "approve" })}>تأیید و اعمال اختلاف</Button>}
                    </Stack>}</TableCell>
                </TableRow>)}</TableBody></Table></TableContainer>}
                <Typography variant="h6" sx={{ fontWeight: 700 }}>تاریخچه گردش کالا</Typography>
                <Paper elevation={0} sx={toolbarSurfaceSx}>
                    <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ alignItems: { md: "center" }, flexWrap: { md: "wrap" } }}>
                        <TextField select label="نوع گردش" value={movementType} onChange={(event) => setMovementType(event.target.value)} sx={operationFieldSx}><MenuItem value="">همه</MenuItem>{Object.entries(movementLabels).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}</TextField>
                        <TextField select label="انبار" value={movementWarehouse} onChange={(event) => setMovementWarehouse(event.target.value)} sx={operationFieldSx}><MenuItem value="">همه انبارها</MenuItem>{(warehouses.data ?? []).map((row) => <MenuItem key={row.id} value={row.id}>{row.name}</MenuItem>)}</TextField>
                        <TextField select label="نوع ماده" value={movementMaterialType} onChange={(event) => setMovementMaterialType(event.target.value as "" | "raw" | "compound")} sx={operationFieldSx}><MenuItem value="">همه انواع</MenuItem><MenuItem value="raw">مواد اولیه</MenuItem><MenuItem value="compound">مواد مرکب</MenuItem></TextField>
                        <TextField label="جستجوی نام ماده" value={movementSearch} onChange={(event) => setMovementSearch(event.target.value)} sx={operationFieldSx} />
                        <TextField select label="ماده" value={movementItem} onChange={(event) => setMovementItem(event.target.value)} sx={operationFieldSx}><MenuItem value="">همه مواد</MenuItem>{(items.data ?? []).filter((row) => !movementMaterialType || row.preparation_level === (movementMaterialType === "raw" ? "raw" : "semi_prepared")).map((row) => <MenuItem key={row.id} value={row.id}>{row.name}</MenuItem>)}</TextField>
                        <TextField label="شناسه سند" value={movementReference} onChange={(event) => setMovementReference(event.target.value)} sx={operationFieldSx} />
                    </Stack>
                </Paper>
                    {!!movements.error && <Alert severity="error">دریافت تاریخچه گردش ناموفق بود.</Alert>}
                    {movements.isLoading && <Paper elevation={0} sx={{ ...sectionSurfaceSx, p: 2 }} role="status" aria-label="در حال بارگذاری تاریخچه"><Skeleton width="25%" height={32} />{Array.from({ length: 5 }).map((_, index) => <Skeleton key={index} height={42} />)}</Paper>}
                    {!movements.isLoading && !movements.error && !movements.data?.length && <Paper elevation={0} sx={{ py: 6, px: 3, border: "1px dashed", borderColor: "divider", borderRadius: 3 }}><Stack spacing={2} sx={{ alignItems: "center", textAlign: "center" }}><Inventory2RoundedIcon sx={{ fontSize: 36, color: "text.secondary" }} /><Typography variant="h6" sx={{ fontWeight: 700 }}>گردشی با این مشخصات پیدا نشد</Typography><Typography variant="body2" color="text.secondary">فیلترها را تغییر دهید تا سوابق مرتبط نمایش داده شوند.</Typography></Stack></Paper>}
                    {!!movements.data?.length && <TableContainer component={Paper} elevation={0} sx={{ ...sectionSurfaceSx, overflowX: "auto", overflowY: "hidden" }}><Table aria-label="تاریخچه گردش کالا" sx={{ minWidth: 760 }}><OperationTableHead columns={["نوع", "ماده و انبار", "مقدار", "مانده پس از گردش", "سند"]} /><TableBody>{movements.data.map((row) => <TableRow key={row.id} hover sx={{ "&:last-child td": { borderBottom: 0 } }}>
                        <TableCell>{movementLabels[row.type] ?? "گردش دیگر"} ({row.direction === "in" ? "ورودی" : "خروجی"})</TableCell>
                        <TableCell>{row.ingredient_name} · {row.material_type === "compound" ? "مواد مرکب" : "مواد اولیه"} · {row.warehouse_name}</TableCell>
                        <TableCell dir="ltr">{row.quantity} {unitLabels[row.unit] ?? row.unit}</TableCell>
                        <TableCell dir="ltr">{row.balance_after}</TableCell>
                        <TableCell>
                            {row.source_type === "inventory_opening_stock"
                                ? <Button size="small" onClick={() => setOpeningDocumentId(row.source_document_id)}>سند موجودی اولیه #{row.source_document_id}</Button>
                                : `#${row.source_document_id}`}
                            {row.reason ? ` · ${row.reason}` : ""}
                        </TableCell>
                    </TableRow>)}</TableBody></Table></TableContainer>}
                <Dialog open={openingDocumentId !== null} onClose={() => setOpeningDocumentId(null)} fullWidth maxWidth="sm" aria-labelledby="opening-stock-detail-title">
                    <DialogTitle id="opening-stock-detail-title">جزئیات سند موجودی اولیه</DialogTitle>
                    <DialogContent dividers>
                        {openingDocument.isLoading && <Box role="status" sx={{ display: "flex", justifyContent: "center", py: 3 }}><CircularProgress /></Box>}
                        {openingDocument.error && <Alert severity="error">دریافت سند ناموفق بود: {errorMessage(openingDocument.error)}</Alert>}
                        {openingDocument.data && <Stack spacing={1}>
                            <Typography>شناسه: {openingDocument.data.id}</Typography>
                            <Typography>انبار: {openingDocument.data.warehouse_name}</Typography>
                            <Typography>مرجع: {openingDocument.data.reference || "—"}</Typography>
                            <Typography>توضیحات: {openingDocument.data.reason || "—"}</Typography>
                            <Typography>یادداشت: {openingDocument.data.notes || "—"}</Typography>
                            <Typography variant="subtitle2" sx={{ pt: 1 }}>مواد ثبت‌شده</Typography>
                            {openingDocument.data.lines.map((line) => <Typography key={line.id} variant="body2">{line.ingredient_name}: {line.quantity} {unitLabels[line.unit] ?? line.unit}</Typography>)}
                        </Stack>}
                    </DialogContent>
                    <DialogActions><Button onClick={() => setOpeningDocumentId(null)}>بستن</Button></DialogActions>
                </Dialog>
            </>}
        </Stack>
    </Box>;
};
