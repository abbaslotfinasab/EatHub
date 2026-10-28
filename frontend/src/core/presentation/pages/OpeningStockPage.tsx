import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
    Alert, Box, Button, CircularProgress, Container, IconButton, MenuItem,
    Paper, Stack, Table, TableBody, TableCell, TableContainer, TableHead,
    TableRow, TextField, Typography,
} from "@mui/material";
import DeleteOutlinedIcon from "@mui/icons-material/DeleteOutlined";
import { apiClient } from "../../data/http/http-client";
import { useAuthStore } from "../store/auth.store";

type Item = { id: number; name: string; unit: string; preparation_level: "raw" | "semi_prepared" };
type Warehouse = { id: number; name: string; is_active: boolean };
type Page<T> = { count: number; page: number; page_size: number; results: T[] };
type DraftLine = { ingredient_id: number; ingredient_name: string; material_type: "raw" | "compound"; stock_unit: string; unit: string; quantity: string; unit_cost: string };
type OpeningStockResponse = { id: number; status: string; lines: Array<{ id: number; ingredient_name: string; quantity: string; unit: string }> };

const unitLabels: Record<string, string> = { kg: "کیلوگرم", g: "گرم", l: "لیتر", ml: "میلی‌لیتر", pc: "عدد", pk: "بسته" };
const compatibleUnits = (unit: string): string[] => {
    if (unit === "kg" || unit === "g") return ["kg", "g"];
    if (unit === "l" || unit === "ml") return ["l", "ml"];
    return [unit];
};

const validDecimalText = (value: string, maxIntegerDigits: number, maxScale: number, allowZero: boolean): boolean => {
    const trimmed = value.trim();
    if (!/^\+?(?:\d+(?:\.\d*)?|\.\d+)$/.test(trimmed)) return false;
    const [integer = "", fraction = ""] = trimmed.replace(/^\+/, "").split(".");
    const significantInteger = integer.replace(/^0+/, "");
    if (significantInteger.length > maxIntegerDigits || fraction.length > maxScale) return false;
    return allowZero || /[1-9]/.test(trimmed);
};

const fetchAllPages = async <T,>(path: string, params: Record<string, unknown>): Promise<T[]> => {
    const pageSize = 100;
    const first = (await apiClient.get<Page<T>>(path, { params: { ...params, page: 1, page_size: pageSize } })).data;
    const pages = Math.ceil(first.count / pageSize);
    const results = [...first.results];
    for (let page = 2; page <= pages; page += 1) {
        const next = (await apiClient.get<Page<T>>(path, { params: { ...params, page, page_size: pageSize } })).data;
        results.push(...next.results);
        if (next.results.length < pageSize) break;
    }
    return results;
};

const errorMessage = (error: unknown): string => {
    const data = (error as { response?: { data?: unknown } })?.response?.data;
    const collect = (value: unknown): string[] => {
        if (typeof value === "string") return [value];
        if (Array.isArray(value)) return value.flatMap(collect);
        if (value && typeof value === "object") return Object.values(value as Record<string, unknown>).flatMap(collect);
        return [];
    };
    const messages = collect(data);
    return messages.length ? messages.join(" ") : error instanceof Error ? error.message : "ثبت موجودی اولیه ناموفق بود. دوباره تلاش کنید.";
};

export const OpeningStockPage = () => {
    const me = useAuthStore((state) => state.me);
    const accessToken = useAuthStore((state) => state.accessToken);
    const permissions = me?.active_business?.permissions ?? [];
    const canView = permissions.includes("inventory.view");
    const canAdjust = permissions.includes("inventory.adjust");
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [warehouseId, setWarehouseId] = useState("");
    const [itemId, setItemId] = useState("");
    const [materialType, setMaterialType] = useState<"raw" | "compound">("raw");
    const [quantity, setQuantity] = useState("");
    const [unit, setUnit] = useState("");
    const [unitCost, setUnitCost] = useState("");
    const [reference, setReference] = useState("");
    const [reason, setReason] = useState("");
    const [draftLines, setDraftLines] = useState<DraftLine[]>([]);
    const [message, setMessage] = useState<{ kind: "success" | "error" | "info"; text: string } | null>(null);

    const queryScope = [me?.id ?? null, me?.active_business?.id ?? null] as const;
    const items = useQuery({
        queryKey: ["inventory-opening-items", ...queryScope],
        enabled: Boolean(accessToken && canView && me?.active_business?.id),
        queryFn: () => fetchAllPages<Item>("/inventory/items/", { is_active: true }),
    });
    const warehouses = useQuery({
        queryKey: ["inventory-opening-warehouses", ...queryScope],
        enabled: Boolean(accessToken && canView && me?.active_business?.id),
        queryFn: () => fetchAllPages<Warehouse>("/inventory/warehouses/", { is_active: true }),
    });
    const selectedItem = useMemo(() => items.data?.find((item) => item.id === Number(itemId)), [items.data, itemId]);

    const submit = useMutation({
        mutationFn: async () => {
            if (!warehouseId || draftLines.length === 0) throw new Error("انبار و دست‌کم یک ردیف را انتخاب کنید.");
            return (await apiClient.post<OpeningStockResponse>("/inventory/opening-stock/", {
                warehouse_id: Number(warehouseId), reference, reason,
                lines: draftLines.map((line) => ({
                    ingredient_id: line.ingredient_id,
                    material_type: line.material_type,
                    quantity: line.quantity,
                    unit: line.unit,
                    unit_cost: line.unit_cost,
                })),
            })).data;
        },
        onSuccess: async (result) => {
            await Promise.all([
                queryClient.invalidateQueries({ queryKey: ["inventory-stock-balances"] }),
                queryClient.invalidateQueries({ queryKey: ["inventory-movement-history"] }),
                queryClient.invalidateQueries({ queryKey: ["inventory-operations"] }),
            ]);
            setMessage({ kind: "success", text: `موجودی اولیه ثبت شد. شماره سند: ${result.id}` });
            setDraftLines([]);
            setReference("");
            setReason("");
        },
        onError: (error: unknown) => setMessage({ kind: "error", text: errorMessage(error) }),
    });

    const addLine = () => {
        if (!selectedItem) { setMessage({ kind: "error", text: "یک ماده از نوع انتخاب‌شده وارد کنید." }); return; }
        if (!validDecimalText(quantity, 24, 12, false)) { setMessage({ kind: "error", text: "مقدار باید مثبت و حداکثر با ۱۲ رقم اعشار وارد شود." }); return; }
        if (!validDecimalText(unitCost, 22, 48, true)) { setMessage({ kind: "error", text: "بهای واحد باید نامنفی و حداکثر با ۴۸ رقم اعشار باشد؛ برای هزینه صفر مقدار ۰ بنویسید." }); return; }
        if (draftLines.some((line) => line.ingredient_id === selectedItem.id)) { setMessage({ kind: "error", text: "هر ماده فقط یک‌بار در هر ثبت مجاز است." }); return; }
        setDraftLines((current) => [...current, {
            ingredient_id: selectedItem.id, ingredient_name: selectedItem.name, material_type: materialType,
            stock_unit: selectedItem.unit, unit: unit || selectedItem.unit,
            quantity, unit_cost: unitCost,
        }]);
        setItemId(""); setQuantity(""); setUnit(""); setUnitCost(""); setMessage(null);
    };

    const loading = items.isLoading || warehouses.isLoading;
    const loadError = items.error || warehouses.error;

    return <Container maxWidth="xl" sx={{ py: 2, pb: 5 }} dir="rtl">
        <Stack spacing={2.5}>
            <Box>
                <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>ثبت موجودی اولیه</Typography>
                <Typography color="text.secondary" sx={{ mt: 0.5 }}>ثبت موجودی آغازین برای مواد موجود در یک انبار؛ این عملیات خرید یا دریافت کالا نیست.</Typography>
            </Box>
            {!canView && <Alert severity="error">اجازه مشاهده موجودی را ندارید.</Alert>}
            {canView && !canAdjust && <Alert severity="warning">برای ثبت موجودی اولیه به مجوز «تعدیل موجودی» نیاز دارید.</Alert>}
            {loadError && <Alert severity="error" action={<Button color="inherit" onClick={() => { void items.refetch(); void warehouses.refetch(); }}>تلاش دوباره</Button>}>بارگذاری مواد اولیه یا انبارها ناموفق بود: {errorMessage(loadError)}</Alert>}
            {message && <Alert severity={message.kind} onClose={() => setMessage(null)}>{message.text}</Alert>}
            {loading && <Box role="status" sx={{ display: "flex", justifyContent: "center", py: 5 }}><CircularProgress /></Box>}
            {canView && !loading && !loadError && !warehouses.data?.length && <Alert severity="info">انبار فعالی برای این کسب‌وکار پیدا نشد.</Alert>}
            {canView && !loading && !loadError && !items.data?.length && <Alert severity="info">ماده فعالی برای ثبت موجودی پیدا نشد.</Alert>}
            {canView && canAdjust && !loading && !loadError && <>
                <Paper sx={{ p: 2 }}>
                    <Stack spacing={2}>
                        <Typography variant="h6">اطلاعات ثبت</Typography>
                        <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                            <TextField select required label="انبار" value={warehouseId} onChange={(event) => setWarehouseId(event.target.value)} sx={{ minWidth: { md: 220 } }}>
                                {(warehouses.data ?? []).map((warehouse) => <MenuItem key={warehouse.id} value={warehouse.id}>{warehouse.name}</MenuItem>)}
                            </TextField>
                            <TextField label="شماره یا مرجع سند" value={reference} onChange={(event) => setReference(event.target.value)} />
                            <TextField label="توضیحات" value={reason} onChange={(event) => setReason(event.target.value)} />
                        </Stack>
                    </Stack>
                </Paper>

                <Paper sx={{ p: 2 }}>
                    <Stack spacing={2}>
                        <Typography variant="h6">افزودن ماده</Typography>
                        <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                            <TextField select label="نوع ماده" value={materialType} onChange={(event) => { setMaterialType(event.target.value as "raw" | "compound"); setItemId(""); setUnit(""); }} sx={{ minWidth: { md: 170 } }}>
                                <MenuItem value="raw">مواد اولیه</MenuItem><MenuItem value="compound">مواد مرکب</MenuItem>
                            </TextField>
                            <TextField select label={materialType === "raw" ? "ماده اولیه" : "ماده مرکب"} value={itemId} onChange={(event) => { setItemId(event.target.value); setUnit(""); }} sx={{ minWidth: { md: 230 } }}>
                                {(items.data ?? []).filter((item) => item.preparation_level === (materialType === "raw" ? "raw" : "semi_prepared") && !draftLines.some((line) => line.ingredient_id === item.id)).map((item) => <MenuItem key={item.id} value={item.id}>{item.name} · {unitLabels[item.unit] ?? item.unit}</MenuItem>)}
                            </TextField>
                            <TextField label="مقدار" type="number" value={quantity} onChange={(event) => setQuantity(event.target.value)} slotProps={{ htmlInput: { min: 0, step: "any", inputMode: "decimal" } }} />
                            <TextField select label="واحد مقدار" value={unit || selectedItem?.unit || ""} onChange={(event) => setUnit(event.target.value)} disabled={!selectedItem} sx={{ minWidth: 150 }}>
                                {selectedItem && compatibleUnits(selectedItem.unit).map((entry) => <MenuItem key={entry} value={entry}>{unitLabels[entry] ?? entry}</MenuItem>)}
                            </TextField>
                            <TextField label={`بهای هر ${unitLabels[selectedItem?.unit ?? ""] ?? selectedItem?.unit ?? "واحد"} (هزینه صفر: ۰)`} type="number" value={unitCost} onChange={(event) => setUnitCost(event.target.value)} slotProps={{ htmlInput: { min: 0, step: "any", inputMode: "decimal" } }} />
                            <Button type="button" variant="outlined" onClick={addLine} disabled={!selectedItem}>افزودن ردیف</Button>
                        </Stack>
                        <Typography variant="caption" color="text.secondary">مقدار می‌تواند با واحد سازگار وارد شود؛ بهای واحد همیشه بر اساس واحد اصلی ماده ثبت می‌شود.</Typography>
                        <Typography variant="caption" color="text.secondary">ارز در موجودی V1 جداگانه ذخیره نمی‌شود؛ مبلغ را با واحد پول مورد استفاده در حسابداری کسب‌وکار وارد کنید.</Typography>
                    </Stack>
                </Paper>

                <Paper sx={{ p: 2 }}>
                    <Stack spacing={1.5}>
                        <Typography variant="h6">بازبینی پیش از ثبت · {draftLines.length} ردیف</Typography>
                        {!draftLines.length && <Alert severity="info">هنوز ماده‌ای به ثبت اضافه نشده است.</Alert>}
                        {!!draftLines.length && <TableContainer sx={{ overflowX: "auto" }}><Table size="small" aria-label="بازبینی موجودی اولیه"><TableHead><TableRow><TableCell>نام ماده</TableCell><TableCell>نوع</TableCell><TableCell>مقدار</TableCell><TableCell>بهای واحد اصلی</TableCell><TableCell align="center">حذف</TableCell></TableRow></TableHead><TableBody>
                            {draftLines.map((line) => <TableRow key={line.ingredient_id}>
                                <TableCell>{line.ingredient_name}</TableCell>
                                <TableCell>{line.material_type === "raw" ? "مواد اولیه" : "مواد مرکب"}</TableCell>
                                <TableCell dir="ltr">{line.quantity} {unitLabels[line.unit] ?? line.unit}</TableCell>
                                <TableCell dir="ltr">{line.unit_cost} / {unitLabels[line.stock_unit] ?? line.stock_unit}</TableCell>
                                <TableCell align="center"><IconButton aria-label={`حذف ${line.ingredient_name}`} onClick={() => setDraftLines((current) => current.filter((entry) => entry.ingredient_id !== line.ingredient_id))}><DeleteOutlinedIcon /></IconButton></TableCell>
                            </TableRow>)}
                        </TableBody></Table></TableContainer>}
                        <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ justifyContent: "flex-start", pt: 1 }}>
                            <Button type="button" onClick={() => navigate("/inventory")}>بازگشت به موجودی</Button>
                            <Button variant="contained" disabled={submit.isPending || !warehouseId || draftLines.length === 0} onClick={() => submit.mutate()}>
                                {submit.isPending ? "در حال ثبت…" : "ثبت نهایی موجودی اولیه"}
                            </Button>
                            {message?.kind === "success" && <Button onClick={() => navigate("/inventory")}>مشاهده موجودی‌ها</Button>}
                        </Stack>
                    </Stack>
                </Paper>
            </>}
        </Stack>
    </Container>;
};
