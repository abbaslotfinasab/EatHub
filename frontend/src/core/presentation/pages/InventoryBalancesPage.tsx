import { useEffect, useState } from "react";
import {
    Alert,
    Box,
    Button,
    CircularProgress,
    Container,
    MenuItem,
    Pagination,
    Paper,
    Stack,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TextField,
    Typography,
} from "@mui/material";
import type { StockBalanceFilters } from "../../domain/entities/inventory/StockBalance";
import { useStockBalances } from "../hooks/useStockBalances";

const PAGE_SIZES = [10, 20, 50, 100];

const formatDecimal = (value: string): string => {
    if (!value.includes(".")) return value;
    const formatted = value.replace(/0+$/, "").replace(/\.$/, "");
    return formatted || "0";
};

const optionalPositiveId = (value: string): number | undefined => {
    if (!value.trim()) return undefined;
    const parsed = Number(value);
    return Number.isInteger(parsed) && parsed > 0 ? parsed : Number.NaN;
};

export const InventoryBalancesPage = () => {
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(20);
    const [ingredientInput, setIngredientInput] = useState("");
    const [warehouseInput, setWarehouseInput] = useState("");
    const [filters, setFilters] = useState<StockBalanceFilters>({
        page: 1,
        pageSize: 20,
    });
    const {
        data,
        isLoading,
        isError,
        isPlaceholderData,
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

    const applyFilters = () => {
        const ingredientId = optionalPositiveId(ingredientInput);
        const warehouseId = optionalPositiveId(warehouseInput);
        setPage(1);
        setFilters({
            page: 1,
            pageSize,
            ...(ingredientId !== undefined ? { ingredientId } : {}),
            ...(warehouseId !== undefined ? { warehouseId } : {}),
        });
    };

    const changePageSize = (nextPageSize: number) => {
        setPageSize(nextPageSize);
        setPage(1);
        setFilters((current) => ({
            ...current,
            page: 1,
            pageSize: nextPageSize,
        }));
    };

    return (
        <Container maxWidth="xl" sx={{ py: 2 }}>
            <Stack spacing={2.5}>
                <Box>
                    <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>
                        موجودی انبار
                    </Typography>
                    <Typography color="text.secondary" sx={{ mt: 0.5 }}>
                        موجودی ثبت‌شده به تفکیک ماده اولیه و انبار
                    </Typography>
                </Box>

                <Paper component="form" onSubmit={(event) => { event.preventDefault(); applyFilters(); }} sx={{ p: 2 }}>
                    <Stack
                        direction={{ xs: "column", md: "row" }}
                        spacing={2}
                        sx={{ alignItems: { md: "center" } }}
                    >
                        <TextField
                            label="شناسه ماده اولیه"
                            type="number"
                            value={ingredientInput}
                            onChange={(event) => setIngredientInput(event.target.value)}
                            slotProps={{ htmlInput: { min: 1, step: 1 } }}
                            size="small"
                        />
                        <TextField
                            label="شناسه انبار"
                            type="number"
                            value={warehouseInput}
                            onChange={(event) => setWarehouseInput(event.target.value)}
                            slotProps={{ htmlInput: { min: 1, step: 1 } }}
                            size="small"
                        />
                        <TextField
                            select
                            label="تعداد در هر صفحه"
                            value={pageSize}
                            onChange={(event) => changePageSize(Number(event.target.value))}
                            size="small"
                            sx={{ minWidth: 170 }}
                        >
                            {PAGE_SIZES.map((size) => (
                                <MenuItem key={size} value={size}>{size}</MenuItem>
                            ))}
                        </TextField>
                        <Button type="submit" variant="contained">اعمال فیلتر</Button>
                    </Stack>
                </Paper>

                {isLoadingResults && (
                    <Box role="status" sx={{ display: "flex", justifyContent: "center", py: 6 }}>
                        <CircularProgress />
                    </Box>
                )}

                {isError && (
                    <Alert severity="error">
                        دریافت موجودی انبار ناموفق بود. ورودی فیلترها را بررسی و دوباره تلاش کنید.
                    </Alert>
                )}

                {!isLoadingResults && !isError && data?.results.length === 0 && (
                    <Alert severity="info">موجودی‌ای برای این فیلترها پیدا نشد.</Alert>
                )}

                {!isLoadingResults && !isError && data && data.results.length > 0 && (
                    <>
                        <TableContainer component={Paper}>
                            <Table aria-label="موجودی انبار">
                                <TableHead>
                                    <TableRow>
                                        <TableCell>ماده اولیه</TableCell>
                                        <TableCell>انبار</TableCell>
                                        <TableCell align="right">موجودی</TableCell>
                                        <TableCell align="right">میانگین بهای واحد</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {data.results.map((balance) => (
                                        <TableRow key={balance.id} hover>
                                            <TableCell>
                                                {balance.ingredientName}
                                                <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                                                    #{balance.ingredientId}
                                                </Typography>
                                            </TableCell>
                                            <TableCell>
                                                {balance.warehouseName}
                                                <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                                                    #{balance.warehouseId}
                                                </Typography>
                                            </TableCell>
                                            <TableCell align="right" dir="ltr">
                                                {formatDecimal(balance.quantity)} {balance.unit}
                                            </TableCell>
                                            <TableCell align="right" dir="ltr">
                                                {formatDecimal(balance.averageCost)} / {balance.unit}
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>

                    </>
                )}

                {!isError && data && (
                    <Stack
                        direction="row"
                        sx={{ justifyContent: "space-between", alignItems: "center" }}
                    >
                        <Typography color="text.secondary">
                            تعداد کل: {data.count}
                        </Typography>
                        <Pagination
                            page={safePage}
                            count={pageCount}
                            disabled={data.count === 0}
                            onChange={(_event, nextPage) => {
                                setPage(nextPage);
                                setFilters((current) => ({ ...current, page: nextPage }));
                            }}
                            color="primary"
                        />
                    </Stack>
                )}
            </Stack>
        </Container>
    );
};
