import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
    Alert, Box, Button, Card, CardContent, CircularProgress, Container, MenuItem,
    Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography,
} from '@mui/material';
import { listAccountsPayables } from '../../../data/di/accountsPayable.ts';
import { listPurchaseSuppliersManagement } from '../../../data/di/purchaseSupplier.ts';
import type { AccountsPayableFilters } from '../../../domain/entities/inventory/AccountsPayable.ts';
import { useAuthStore } from '../../store/auth.store.ts';

const statusLabels: Record<string, string> = {
    open: 'باز',
    partially_paid: 'پرداخت جزئی',
    paid: 'تسویه‌شده',
    cancelled: 'لغوشده',
};
const money = (value: string) => Number(value || 0).toLocaleString('fa-IR', { maximumFractionDigits: 2 });
const dateLabel = (value: string | null) => value
    ? new Date(`${value}T00:00:00`).toLocaleDateString('fa-IR')
    : 'بدون سررسید';
const errorMessage = (error: unknown) => {
    const response = (error as { response?: { status?: number } })?.response;
    if (response?.status === 403) return 'مجوز مشاهده اطلاعات مالی را ندارید.';
    if (response?.status === 404) return 'منبع موردنظر پیدا نشد.';
    return 'دریافت اطلاعات ناموفق بود؛ اتصال را بررسی و دوباره تلاش کنید.';
};

export const AccountsPayablePage = () => {
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    const permissions = useAuthStore((state) => state.me?.active_business?.permissions ?? []);
    const canView = permissions.includes('purchase.view');

    const [status, setStatus] = useState('all');
    const [supplierId, setSupplierId] = useState('');
    const [dueDateFrom, setDueDateFrom] = useState('');
    const [dueDateTo, setDueDateTo] = useState('');
    const [search, setSearch] = useState('');

    const filters = useMemo<AccountsPayableFilters>(() => ({
        ...(status === 'all' ? {} : { status: status as AccountsPayableFilters['status'] }),
        ...(supplierId ? { supplierId } : {}),
        ...(dueDateFrom ? { dueDateFrom } : {}),
        ...(dueDateTo ? { dueDateTo } : {}),
    }), [status, supplierId, dueDateFrom, dueDateTo]);

    const payables = useQuery({
        queryKey: ['accounts-payables', userId, businessId, filters],
        queryFn: () => listAccountsPayables.execute(filters),
        enabled: Boolean(canView && userId !== null && businessId !== null),
    });
    const suppliers = useQuery({
        queryKey: ['purchase-suppliers', userId, businessId, 'accounts-payable-filter'],
        queryFn: () => listPurchaseSuppliersManagement.execute(),
        enabled: Boolean(canView && userId !== null && businessId !== null),
    });

    const supplierNames = useMemo(
        () => new Map((suppliers.data ?? []).map((supplier) => [supplier.id, supplier.name])),
        [suppliers.data],
    );
    const filtered = useMemo(() => (payables.data ?? []).filter((payable) => {
        const term = search.trim().toLocaleLowerCase();
        return !term
            || (payable.invoiceNumber ?? '').toLocaleLowerCase().includes(term)
            || (payable.supplierName ?? supplierNames.get(payable.supplierId) ?? '').toLocaleLowerCase().includes(term)
            || payable.id.includes(term);
    }), [payables.data, search, supplierNames]);

    const totals = useMemo(() => filtered.reduce((result, payable) => {
        result.amount += Number(payable.amount);
        result.allocated += Number(payable.allocatedAmount);
        if (payable.status !== 'cancelled') result.outstanding += Number(payable.outstandingAmount);
        return result;
    }, { amount: 0, allocated: 0, outstanding: 0 }), [filtered]);

    const resetFilters = () => {
        setStatus('all');
        setSupplierId('');
        setDueDateFrom('');
        setDueDateTo('');
        setSearch('');
    };

    return (
        <Container maxWidth="xl" dir="rtl" sx={{ py: 3 }}>
            <Stack spacing={2.5}>
                <Box>
                    <Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>حساب‌های پرداختنی</Typography>
                    <Typography color="text.secondary">مانده بدهی تأمین‌کنندگان بر اساس فاکتورهای ثبت مالی‌شده</Typography>
                </Box>

                {!canView && <Alert severity="error">برای مشاهده حساب‌های پرداختنی، مجوز مشاهده خرید لازم است.</Alert>}

                {payables.isLoading && <Box role="status" sx={{ display: 'flex', justifyContent: 'center', py: 5 }}><CircularProgress /></Box>}
                {payables.isError && <Alert severity="error" action={<Button color="inherit" size="small" onClick={() => { void Promise.all([payables.refetch(), suppliers.refetch()]); }}>تلاش مجدد</Button>}>دریافت حساب‌های پرداختنی ناموفق بود. {errorMessage(payables.error)}</Alert>}
                {suppliers.isError && <Alert severity="warning" action={<Button color="inherit" size="small" onClick={() => { void suppliers.refetch(); }}>تلاش مجدد</Button>}>فهرست تأمین‌کنندگان بارگذاری نشد؛ شناسه تأمین‌کننده نمایش داده می‌شود.</Alert>}

                {!payables.isLoading && !payables.isError && canView && <>
                    <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
                        <Card sx={{ flex: 1 }}><CardContent><Typography color="text.secondary" variant="body2">جمع مبلغ فاکتورها</Typography><Typography variant="h5" sx={{ fontWeight: 700 }}>{money(String(totals.amount))}</Typography></CardContent></Card>
                        <Card sx={{ flex: 1 }}><CardContent><Typography color="text.secondary" variant="body2">جمع تخصیص پرداخت</Typography><Typography variant="h5" sx={{ fontWeight: 700 }}>{money(String(totals.allocated))}</Typography></CardContent></Card>
                        <Card sx={{ flex: 1 }}><CardContent><Typography color="text.secondary" variant="body2">مانده بدهی</Typography><Typography variant="h5" sx={{ fontWeight: 700 }}>{money(String(totals.outstanding))}</Typography></CardContent></Card>
                    </Stack>

                    <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
                        <TextField fullWidth label="جستجو بر اساس شماره فاکتور یا تأمین‌کننده" value={search} onChange={(event) => setSearch(event.target.value)} />
                        <TextField select label="وضعیت" value={status} onChange={(event) => setStatus(event.target.value)} sx={{ minWidth: { md: 180 } }}>
                            <MenuItem value="all">همه وضعیت‌ها</MenuItem>
                            {Object.entries(statusLabels).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
                        </TextField>
                        <TextField select label="تأمین‌کننده" value={supplierId} onChange={(event) => setSupplierId(event.target.value)} sx={{ minWidth: { md: 220 } }}>
                            <MenuItem value="">همه تأمین‌کنندگان</MenuItem>
                            {(suppliers.data ?? []).map((supplier) => <MenuItem key={supplier.id} value={supplier.id}>{supplier.name}</MenuItem>)}
                        </TextField>
                    </Stack>
                    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} sx={{ alignItems: { sm: 'center' } }}>
                        <TextField type="date" label="سررسید از" value={dueDateFrom} onChange={(event) => setDueDateFrom(event.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
                        <TextField type="date" label="سررسید تا" value={dueDateTo} onChange={(event) => setDueDateTo(event.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
                        <Button onClick={resetFilters}>پاک‌کردن فیلترها</Button>
                    </Stack>

                    {filtered.length > 0 ? <Paper sx={{ overflowX: 'auto' }}>
                        <Table aria-label="حساب‌های پرداختنی">
                            <TableHead><TableRow>
                                <TableCell>شماره فاکتور</TableCell><TableCell>تأمین‌کننده</TableCell><TableCell>سررسید</TableCell>
                                <TableCell>مبلغ</TableCell><TableCell>پرداخت‌شده</TableCell><TableCell>مانده</TableCell><TableCell>وضعیت</TableCell>
                            </TableRow></TableHead>
                            <TableBody>{filtered.map((payable) => <TableRow key={payable.id} hover>
                                <TableCell>{payable.invoiceNumber ?? `فاکتور #${payable.sourceInvoiceId}`}</TableCell>
                                <TableCell>{payable.supplierName ?? supplierNames.get(payable.supplierId) ?? `تأمین‌کننده #${payable.supplierId}`}</TableCell>
                                <TableCell>{dateLabel(payable.dueDate)}</TableCell>
                                <TableCell>{money(payable.amount)}</TableCell>
                                <TableCell>{money(payable.allocatedAmount)}</TableCell>
                                <TableCell sx={{ fontWeight: 700 }}>{money(payable.outstandingAmount)}</TableCell>
                                <TableCell>{statusLabels[payable.status] ?? payable.status}</TableCell>
                            </TableRow>)}</TableBody>
                        </Table>
                    </Paper> : <Alert severity="info">{payables.data?.length ? 'با فیلترهای انتخاب‌شده موردی پیدا نشد.' : 'هنوز حساب پرداختنی ثبت نشده است. با ثبت مالی فاکتور خرید، بدهی ایجاد می‌شود.'}</Alert>}
                </>}
            </Stack>
        </Container>
    );
};
