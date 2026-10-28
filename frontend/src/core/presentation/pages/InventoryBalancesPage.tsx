import { useEffect, useState } from "react";
import {
    Alert,
    Box,
    Button,
    Container,
    Fab,
    FormControl,
    InputLabel,
    MenuItem,
    Pagination,
    Paper,
    Select,
    Skeleton,
    Stack,
    Tab,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Tabs,
    TextField,
    Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import Inventory2RoundedIcon from "@mui/icons-material/Inventory2Rounded";
import SearchOffRoundedIcon from "@mui/icons-material/SearchOffRounded";
import { useNavigate, useSearchParams } from "react-router-dom";
import type { SelectChangeEvent } from "@mui/material/Select";
import type { StockBalanceFilters } from "../../domain/entities/inventory/StockBalance";
import { useStockBalances } from "../hooks/useStockBalances";
import { InventoryOperationsPage } from "./InventoryOperationsPage";
import { useAuthStore } from "../store/auth.store";

const PAGE_SIZES = [10, 20, 50, 100];

const filterFieldSx = {
    flex: { md: 1 },
    minWidth: { sm: 180 },
    width: { xs: "100%", md: "auto" },
    "& .MuiOutlinedInput-root": {
        height: 56,
        borderRadius: 1,
        "& fieldset": { borderColor: "#E2E8F0" },
        "&:hover fieldset": { borderColor: "#1F4A33" },
        "&.Mui-focused fieldset": { borderColor: "#10281A", borderWidth: 2 },
    },
};

const formatDecimal = (value: string): string => {
    if (!value.includes(".")) return value;
    const formatted = value.replace(/0+$/, "").replace(/\.$/, "");
    return formatted || "0";
};

const formatUnit = (unit: string): string => ({
    kg: "کیلوگرم", g: "گرم", l: "لیتر", ml: "میلی‌لیتر", pc: "عدد", pk: "بسته",
}[unit] ?? unit);

const optionalPositiveId = (value: string): number | undefined => {
    if (!value.trim()) return undefined;
    const parsed = Number(value);
    return Number.isInteger(parsed) && parsed > 0 ? parsed : Number.NaN;
};

const InventoryBalancesLoading = () => (
    <Stack spacing={3} role="status" aria-label="در حال بارگذاری موجودی">
        <Paper elevation={0} sx={{ p: 2, border: 1, borderColor: "divider", borderRadius: 1 }}>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                <Skeleton variant="rounded" height={56} sx={{ flex: 1 }} />
                <Skeleton variant="rounded" height={56} sx={{ flex: 1 }} />
                <Skeleton variant="rounded" height={56} width={150} />
            </Stack>
        </Paper>
        <TableContainer component={Paper} elevation={0} sx={{ border: 1, borderColor: "divider", borderRadius: 3, overflow: "hidden" }}>
            <Table aria-hidden="true">
                <TableHead><TableRow>{Array.from({ length: 5 }).map((_, index) => <TableCell key={index}><Skeleton width="65%" /></TableCell>)}</TableRow></TableHead>
                <TableBody>{Array.from({ length: 7 }).map((_, row) => <TableRow key={row}>{Array.from({ length: 5 }).map((__, cell) => <TableCell key={cell}><Skeleton height={28} /></TableCell>)}</TableRow>)}</TableBody>
            </Table>
        </TableContainer>
    </Stack>
);

export const InventoryBalancesPage = () => {
    const navigate = useNavigate();
    const canAdjust = useAuthStore((state) => state.me?.active_business?.permissions?.includes("inventory.adjust") ?? false);
    const [searchParams, setSearchParams] = useSearchParams();
    const activeView = searchParams.get("view") === "operations" ? "operations" : "balances";
    const initialWarehouseId = searchParams.get("warehouse_id") ?? "";
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(20);
    const [ingredientInput, setIngredientInput] = useState("");
    const [searchInput, setSearchInput] = useState("");
    const [warehouseInput, setWarehouseInput] = useState(initialWarehouseId);
    const [materialTypeInput, setMaterialTypeInput] = useState<"" | "raw" | "compound">("");
    const [filters, setFilters] = useState<StockBalanceFilters>(() => ({
        page: 1,
        pageSize: 20,
        ...(optionalPositiveId(initialWarehouseId) ? { warehouseId: Number(initialWarehouseId) } : {}),
    }));
    const {
        data,
        isLoading,
        isError,
        isPlaceholderData,
        refetch,
    } = useStockBalances(filters);

    const pageCount = Math.max(1, Math.ceil((data?.count ?? 0) / pageSize));
    const safePage = Math.min(page, pageCount);

    useEffect(() => {
        const responseMatchesRequestedPage =
            data !== undefined &&
            !isPlaceholderData &&
            !isError &&
            data.page === filters.page;

        if (responseMatchesRequestedPage && page > pageCount) {
            // Keep the selected page valid when a filter reduces the result count.
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setPage(safePage);
            setFilters((current) => ({ ...current, page: safePage }));
        }
    }, [data, filters.page, isError, isPlaceholderData, page, pageCount, safePage]);

    const isLoadingResults = isLoading || isPlaceholderData;
    const hasActiveFilters = Boolean(searchInput || ingredientInput || warehouseInput || materialTypeInput);

    const applyFilters = () => {
        const ingredientId = optionalPositiveId(ingredientInput);
        const warehouseId = optionalPositiveId(warehouseInput);
        setPage(1);
        setFilters({
            page: 1,
            pageSize,
            ...(searchInput.trim() ? { search: searchInput.trim() } : {}),
            ...(ingredientId !== undefined ? { ingredientId } : {}),
            ...(warehouseId !== undefined ? { warehouseId } : {}),
            ...(materialTypeInput ? { materialType: materialTypeInput } : {}),
        });
    };

    const resetFilters = () => {
        setIngredientInput("");
        setSearchInput("");
        setWarehouseInput("");
        setMaterialTypeInput("");
        setPage(1);
        setFilters({ page: 1, pageSize });
        const nextParams = new URLSearchParams(searchParams);
        nextParams.delete("warehouse_id");
        setSearchParams(nextParams, { replace: true });
    };

    const changePageSize = (event: SelectChangeEvent<number>) => {
        const nextPageSize = Number(event.target.value);
        setPageSize(nextPageSize);
        setPage(1);
        setFilters((current) => ({ ...current, page: 1, pageSize: nextPageSize }));
    };

    return (
        <Container maxWidth="xl" sx={{ pt: 2, pb: activeView === "balances" && canAdjust ? 12 : 2 }} dir="rtl">
            <Stack spacing={3}>
                <Box>
                    <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>
                        موجودی
                    </Typography>
                    <Typography color="text.secondary" sx={{ mt: 0.5 }}>
                        مانده کالاها و عملیات انبار در یکجا
                    </Typography>
                </Box>

                <Paper elevation={0} sx={{ border: 1, borderColor: "divider", borderRadius: 3, overflow: "hidden" }}>
                    <Tabs
                        value={activeView}
                        onChange={(_event, value: "balances" | "operations") => {
                            const next = new URLSearchParams(searchParams);
                            if (value === "balances") next.delete("view");
                            else next.set("view", value);
                            setSearchParams(next);
                        }}
                        aria-label="بخش‌های موجودی"
                        variant="scrollable"
                        allowScrollButtonsMobile
                        sx={{ px: 1 }}
                    >
                        <Tab value="balances" label="موجودی فعلی" />
                        <Tab value="operations" label="عملیات و گردش کالا" />
                    </Tabs>
                </Paper>

                {activeView === "operations" ? <InventoryOperationsPage embedded /> : <>
                    <Paper
                        component="form"
                        elevation={0}
                        onSubmit={(event) => { event.preventDefault(); applyFilters(); }}
                        sx={{ p: 2, border: 1, borderColor: "divider", borderRadius: 1, bgcolor: "background.paper" }}
                    >
                        <Stack
                            direction={{ xs: "column", md: "row" }}
                            spacing={2}
                            sx={{ alignItems: { md: "center" } }}
                        >
                            <TextField
                                label="جستجوی نام ماده"
                                value={searchInput}
                                onChange={(event) => setSearchInput(event.target.value)}
                                sx={filterFieldSx}
                            />
                            <TextField
                                label="شناسه ماده"
                                type="number"
                                value={ingredientInput}
                                onChange={(event) => setIngredientInput(event.target.value)}
                                slotProps={{ htmlInput: { min: 1, step: 1 } }}
                                sx={filterFieldSx}
                            />
                            <TextField
                                select
                                label="نوع ماده"
                                value={materialTypeInput}
                                onChange={(event) => setMaterialTypeInput(event.target.value as "" | "raw" | "compound")}
                                sx={filterFieldSx}
                            >
                                <MenuItem value="">همه انواع</MenuItem><MenuItem value="raw">مواد اولیه</MenuItem><MenuItem value="compound">مواد مرکب</MenuItem>
                            </TextField>
                            <TextField
                                label="شناسه انبار"
                                type="number"
                                value={warehouseInput}
                                onChange={(event) => setWarehouseInput(event.target.value)}
                                slotProps={{ htmlInput: { min: 1, step: 1 } }}
                                sx={filterFieldSx}
                            />
                            <Button type="submit" variant="contained" sx={{ width: { xs: "100%", md: 150 }, height: 56, borderRadius: 1, flexShrink: 0 }}>
                                اعمال فیلتر
                            </Button>
                            {hasActiveFilters && (
                                <Button type="button" variant="outlined" onClick={resetFilters} sx={{ width: { xs: "100%", md: 150 }, height: 56, borderRadius: 1, flexShrink: 0 }}>
                                    پاک کردن
                                </Button>
                            )}
                        </Stack>
                    </Paper>

                    {isLoadingResults && <InventoryBalancesLoading />}

                    {isError && (
                        <Alert
                            severity="error"
                            action={<Button color="inherit" size="small" onClick={() => void refetch()}>تلاش دوباره</Button>}
                        >
                            دریافت موجودی انبار ناموفق بود. ورودی فیلترها را بررسی و دوباره تلاش کنید.
                        </Alert>
                    )}

                    {!isLoadingResults && !isError && data?.results.length === 0 && (
                        <Paper elevation={0} sx={{ py: 8, px: 4, borderRadius: 3, border: "1px dashed", borderColor: "divider" }}>
                            <Stack sx={{ alignItems: "center", textAlign: "center", gap: 3 }}>
                                <Box sx={{ width: 72, height: 72, display: "flex", alignItems: "center", justifyContent: "center", borderRadius: "50%", bgcolor: "action.hover" }}>
                                    {hasActiveFilters
                                        ? <SearchOffRoundedIcon sx={{ fontSize: 36, color: "text.secondary" }} />
                                        : <Inventory2RoundedIcon sx={{ fontSize: 36, color: "text.secondary" }} />}
                                </Box>
                                <Stack spacing={1}>
                                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                                        {hasActiveFilters ? "موجودی‌ای پیدا نشد" : "هنوز موجودی ثبت نشده است"}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 420 }}>
                                        {hasActiveFilters
                                            ? "با شناسه‌های واردشده موجودی‌ای پیدا نشد. فیلترها را تغییر دهید یا پاک کنید."
                                            : "پس از ثبت موجودی برای مواد اولیه یا مواد مرکب، مانده هر انبار در این بخش نمایش داده می‌شود."}
                                    </Typography>
                                </Stack>
                                {hasActiveFilters && <Button variant="contained" onClick={resetFilters}>پاک کردن فیلترها</Button>}
                            </Stack>
                        </Paper>
                    )}

                    {!isLoadingResults && !isError && data && data.results.length > 0 && (
                        <TableContainer
                            component={Paper}
                            elevation={0}
                            sx={{ border: 1, borderColor: "divider", borderRadius: 3, overflow: "hidden", overflowX: "auto", overflowY: "hidden" }}
                        >
                            <Table aria-label="موجودی انبار" dir="rtl" sx={{ minWidth: 680 }}>
                                <TableHead>
                                    <TableRow>
                                        <TableCell><Typography sx={{ fontWeight: 700 }}>ماده</Typography></TableCell>
                                        <TableCell><Typography sx={{ fontWeight: 700 }}>نوع ماده</Typography></TableCell>
                                        <TableCell><Typography sx={{ fontWeight: 700 }}>انبار</Typography></TableCell>
                                        <TableCell align="right"><Typography sx={{ fontWeight: 700 }}>موجودی</Typography></TableCell>
                                        <TableCell align="right"><Typography sx={{ fontWeight: 700 }}>میانگین بهای واحد</Typography></TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {data.results.map((balance) => (
                                        <TableRow key={balance.id} hover sx={{ "&:last-child td": { borderBottom: 0 } }}>
                                            <TableCell>
                                                {balance.ingredientName}
                                                <Typography component="span" variant="caption" color="text.secondary" sx={{ mr: 1 }} dir="ltr">
                                                    #{balance.ingredientId}
                                                </Typography>
                                            </TableCell>
                                            <TableCell>{balance.materialType === "compound" ? "مواد مرکب" : "مواد اولیه"}</TableCell>
                                            <TableCell>
                                                {balance.warehouseName}
                                                <Typography component="span" variant="caption" color="text.secondary" sx={{ mr: 1 }} dir="ltr">
                                                    #{balance.warehouseId}
                                                </Typography>
                                            </TableCell>
                                            <TableCell align="right" dir="ltr">
                                                {formatDecimal(balance.quantity)} {formatUnit(balance.unit)}
                                            </TableCell>
                                            <TableCell align="right" dir="ltr">
                                                {formatDecimal(balance.averageCost)} / {formatUnit(balance.unit)}
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    )}

                    {!isError && data && (
                        <Paper variant="outlined" sx={{ p: { xs: 1.5, sm: 2 }, borderRadius: 2, direction: "rtl" }}>
                            <Stack
                                sx={{
                                    flexDirection: { xs: "column", sm: "row" },
                                    gap: 2,
                                    alignItems: "center",
                                    justifyContent: "center",
                                }}
                            >
                                <Typography color="text.secondary">تعداد کل: {data.count.toLocaleString("fa-IR")}</Typography>
                                <Pagination
                                    page={safePage}
                                    count={pageCount}
                                    disabled={data.count === 0}
                                    onChange={(_event, nextPage) => {
                                        setPage(nextPage);
                                        setFilters((current) => ({ ...current, page: nextPage }));
                                    }}
                                    shape="rounded"
                                    color="primary"
                                    siblingCount={1}
                                    boundaryCount={1}
                                    aria-label="صفحه‌بندی موجودی"
                                />
                                <FormControl size="small" sx={{ minWidth: 150 }}>
                                    <InputLabel id="inventory-rows-per-page-label">تعداد در صفحه</InputLabel>
                                    <Select
                                        labelId="inventory-rows-per-page-label"
                                        value={pageSize}
                                        label="تعداد در صفحه"
                                        onChange={changePageSize}
                                        inputProps={{ "aria-label": "تعداد در صفحه" }}
                                    >
                                        {PAGE_SIZES.map((size) => <MenuItem key={size} value={size}>{size}</MenuItem>)}
                                    </Select>
                                </FormControl>
                            </Stack>
                        </Paper>
                    )}
                </>}
            </Stack>

            {activeView === "balances" && canAdjust && (
                <Fab
                    variant="extended"
                    aria-label="ثبت موجودی اولیه"
                    onClick={() => navigate("/inventory/opening-stock")}
                    sx={{
                        position: "fixed",
                        left: 24,
                        bottom: 24,
                        bgcolor: "#10281A",
                        color: "#fff",
                        "&:hover": { bgcolor: "#173724" },
                    }}
                >
                    <AddIcon />
                    ثبت موجودی اولیه
                </Fab>
            )}
        </Container>
    );
};
