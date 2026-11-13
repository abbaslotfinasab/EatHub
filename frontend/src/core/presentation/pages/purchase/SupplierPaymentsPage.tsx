import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
    Alert, Box, Button, Card, CardContent, CircularProgress, Container, Dialog, DialogActions,
    DialogContent, DialogTitle, MenuItem, Paper, Stack, Table, TableBody, TableCell, TableHead,
    TableRow, TextField, Typography,
} from '@mui/material';
import { createSupplierPayment, listSupplierPayments } from '../../../data/di/supplierPayment.ts';
import { listPurchaseSuppliersManagement } from '../../../data/di/purchaseSupplier.ts';
import { listAccountsPayables } from '../../../data/di/accountsPayable.ts';
import { createPaymentAllocation, listPaymentAllocations } from '../../../data/di/paymentAllocation.ts';
import type { AccountsPayable } from '../../../domain/entities/inventory/AccountsPayable.ts';
import type { CreatePaymentAllocationInput } from '../../../domain/entities/inventory/PaymentAllocation.ts';
import type {
    CreateSupplierPaymentInput,
    SupplierPaymentFilters,
    SupplierPaymentMethod,
} from '../../../domain/entities/inventory/SupplierPayment.ts';
import type { PendingSupplierPaymentRequest } from '../../utils/supplierPaymentRequestIdentity.ts';
import {
    clearPendingSupplierPayment,
    readPendingSupplierPayment,
    savePendingSupplierPayment,
    supplierPaymentFingerprint,
} from '../../utils/supplierPaymentRequestIdentity.ts';
import { useAuthStore } from '../../store/auth.store.ts';

interface PendingAllocationRequest {
    businessId: string;
    paymentId: string;
    fingerprint: string;
    key: string;
    input: CreatePaymentAllocationInput;
}

const allocationStorageKey = (businessId: string) => `eathub:pending-payment-allocation:${businessId}`;
const readPendingAllocation = (businessId: string): PendingAllocationRequest | null => {
    const raw = window.sessionStorage.getItem(allocationStorageKey(businessId));
    if (!raw) return null;
    const value = JSON.parse(raw) as PendingAllocationRequest;
    if (value.businessId !== businessId || !value.key || !value.input) return null;
    return value;
};
const savePendingAllocation = (request: PendingAllocationRequest) =>
    window.sessionStorage.setItem(allocationStorageKey(request.businessId), JSON.stringify(request));
const clearPendingAllocation = (businessId: string) =>
    window.sessionStorage.removeItem(allocationStorageKey(businessId));

const methodLabels: Record<SupplierPaymentMethod, string> = {
    cash: 'نقدی', bank_transfer: 'انتقال بانکی', card: 'کارت', cheque: 'چک', credit: 'اعتباری', other: 'سایر',
};
const emptyForm: CreateSupplierPaymentInput = { supplierId: '', amount: '', paymentDate: '', method: 'bank_transfer' };
const toMinor = (value: string): bigint => {
    const match = /^(0|[1-9]\d*)(?:\.(\d{1,2}))?$/.exec(value.trim());
    if (!match) return 0n;
    return BigInt(match[1]) * 100n + BigInt((match[2] ?? '').padEnd(2, '0'));
};
const fromMinor = (value: bigint) => (value / 100n).toString() + '.' + (value % 100n).toString().padStart(2, '0');
const money = (value: string) => {
    const minor = toMinor(value);
    const whole = (minor / 100n).toLocaleString('fa-IR');
    const fraction = minor % 100n;
    return fraction ? whole + '٫' + fraction.toString().padStart(2, '0') : whole;
};
const dateLabel = (value: string) => new Date(`${value}T00:00:00`).toLocaleDateString('fa-IR');
const errorMessage = (error: unknown) => {
    const response = (error as { response?: { status?: number; data?: unknown } })?.response;
    if (response?.status === 403) return 'مجوز لازم برای این عملیات را ندارید.';
    if (response?.status === 404) return 'رکورد موردنظر در کسب‌وکار جاری پیدا نشد.';
    if (response?.status === 409) return 'شناسه درخواست با اطلاعات دیگری استفاده شده است.';
    if (response?.data) {
        const flatten = (value: unknown): string[] => {
            if (typeof value === 'string') return [value];
            if (Array.isArray(value)) return value.flatMap(flatten);
            if (value && typeof value === 'object') return Object.values(value).flatMap(flatten);
            return [];
        };
        const details = flatten(response.data);
        if (details.length) return details.join(' ');
    }
    return error instanceof Error ? error.message : 'عملیات ناموفق بود؛ اتصال را بررسی و دوباره تلاش کنید.';
};

export const SupplierPaymentsPage = () => {
    const queryClient = useQueryClient();
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    const permissions = useAuthStore((state) => state.me?.active_business?.permissions ?? []);
    const canView = permissions.includes('purchase.view');
    const canCreate = permissions.includes('purchase.payment.create');
    const canAllocate = permissions.includes('purchase.payment.allocate');

    const [supplierFilter, setSupplierFilter] = useState('');
    const [methodFilter, setMethodFilter] = useState('');
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');
    const [form, setForm] = useState<CreateSupplierPaymentInput>(emptyForm);
    const [pending, setPending] = useState<PendingSupplierPaymentRequest | null>(null);
    const [formError, setFormError] = useState('');
    const [success, setSuccess] = useState('');
    const [allocationPaymentId, setAllocationPaymentId] = useState('');
    const [allocationPayableId, setAllocationPayableId] = useState('');
    const [allocationAmount, setAllocationAmount] = useState('');
    const [allocationError, setAllocationError] = useState('');
    const [pendingAllocation, setPendingAllocation] = useState<PendingAllocationRequest | null>(null);

    const filters = useMemo<SupplierPaymentFilters>(() => ({
        ...(supplierFilter ? { supplierId: supplierFilter } : {}),
        ...(methodFilter ? { method: methodFilter as SupplierPaymentMethod } : {}),
        ...(dateFrom ? { paymentDateFrom: dateFrom } : {}),
        ...(dateTo ? { paymentDateTo: dateTo } : {}),
    }), [supplierFilter, methodFilter, dateFrom, dateTo]);

    const payments = useQuery({
        queryKey: ['supplier-payments', userId, businessId, filters],
        queryFn: () => listSupplierPayments.execute(filters),
        enabled: Boolean(canView && userId !== null && businessId !== null),
    });
    const suppliers = useQuery({
        queryKey: ['purchase-suppliers', userId, businessId, 'supplier-payment-page'],
        queryFn: () => listPurchaseSuppliersManagement.execute(),
        enabled: Boolean(canView && userId !== null && businessId !== null),
    });
    const payables = useQuery({
        queryKey: ['accounts-payables', userId, businessId, 'allocation-options'],
        queryFn: () => listAccountsPayables.execute(),
        enabled: Boolean(allocationPaymentId && canView && userId !== null && businessId !== null),
    });
    const allocationHistory = useQuery({
        queryKey: ['payment-allocations', userId, businessId, allocationPaymentId],
        queryFn: () => listPaymentAllocations.execute(allocationPaymentId),
        enabled: Boolean(allocationPaymentId && canView && userId !== null && businessId !== null),
    });

    useEffect(() => {
        if (!businessId) { setPending(null); setPendingAllocation(null); return; }
        try {
            const restored = readPendingSupplierPayment(String(businessId), window.sessionStorage);
            if (restored) { setPending(restored); setForm(restored.input); }
            setPendingAllocation(readPendingAllocation(String(businessId)));
        } catch {
            setFormError('فضای ذخیره امن درخواست در این مرورگر در دسترس نیست؛ درخواست جدید ارسال نشد.');
        }
    }, [businessId]);

    const refresh = async (paymentId?: string) => {
        await Promise.all([
            queryClient.invalidateQueries({ queryKey: ['supplier-payments', userId, businessId] }),
            queryClient.invalidateQueries({ queryKey: ['accounts-payables', userId, businessId] }),
            ...(paymentId ? [queryClient.invalidateQueries({ queryKey: ['payment-allocations', userId, businessId, paymentId] })] : []),
        ]);
    };

    const paymentMutation = useMutation({
        mutationFn: (request: PendingSupplierPaymentRequest) => createSupplierPayment.execute(request.input, request.key),
        onSuccess: async (payment, request) => {
            try { clearPendingSupplierPayment(request.businessId, window.sessionStorage); } catch { /* server success is authoritative */ }
            setPending(null); setForm(emptyForm); setFormError('');
            setSuccess(`پرداخت شماره ${payment.id} ثبت شد.`);
            await refresh();
        },
        onError: (error) => {
            const status = (error as { response?: { status?: number } })?.response?.status ?? 0;
            if (status >= 400 && status < 500) {
                try { clearPendingSupplierPayment(String(businessId), window.sessionStorage); } catch { /* retain visible error */ }
                setPending(null);
            }
            setFormError(errorMessage(error));
        },
    });

    const allocationMutation = useMutation({
        mutationFn: (request: PendingAllocationRequest) => createPaymentAllocation.execute(request.input, request.key),
        onSuccess: async (_allocation, request) => {
            try { clearPendingAllocation(request.businessId); } catch { /* server success is authoritative */ }
            setPendingAllocation(null);
            setAllocationAmount('');
            setAllocationPayableId('');
            setAllocationError('');
            await refresh(request.paymentId);
        },
        onError: (error) => {
            const status = (error as { response?: { status?: number } })?.response?.status ?? 0;
            if (status >= 400 && status < 500 && businessId) {
                try { clearPendingAllocation(String(businessId)); } catch { /* retain visible error */ }
                setPendingAllocation(null);
            }
            setAllocationError(errorMessage(error));
        },
    });

    const submit = (event: FormEvent) => {
        event.preventDefault(); setFormError(''); setSuccess('');
        if (!businessId || !canCreate) return;
        if (pending) { paymentMutation.mutate(pending); return; }
        const input: CreateSupplierPaymentInput = {
            supplierId: form.supplierId, amount: form.amount.trim(), paymentDate: form.paymentDate, method: form.method,
        };
        const fingerprint = supplierPaymentFingerprint(String(businessId), input);
        if (!globalThis.crypto?.randomUUID) { setFormError('ساخت شناسه امن پرداخت در این مرورگر ممکن نیست.'); return; }
        const request: PendingSupplierPaymentRequest = {
            businessId: String(businessId), fingerprint, key: globalThis.crypto.randomUUID(), input,
        };
        try { savePendingSupplierPayment(request, window.sessionStorage); }
        catch { setFormError('ذخیره شناسه امن پرداخت ناموفق بود؛ درخواست ارسال نشد.'); return; }
        setPending(request); paymentMutation.mutate(request);
    };

    const openAllocation = (paymentId: string) => {
        setAllocationPaymentId(paymentId);
        setAllocationPayableId('');
        setAllocationAmount('');
        setAllocationError('');
        try {
            const restored = businessId ? readPendingAllocation(String(businessId)) : null;
            if (restored?.paymentId === paymentId) setPendingAllocation(restored);
            else setPendingAllocation(null);
        } catch { setAllocationError('بازیابی درخواست تخصیص ناموفق بود.'); }
    };
    const selectedPayment = payments.data?.find((payment) => payment.id === allocationPaymentId);
    const eligiblePayables = (payables.data ?? []).filter((payable) =>
        selectedPayment && payable.supplierId === selectedPayment.supplierId
        && payable.status !== 'cancelled' && toMinor(payable.outstandingAmount) > 0n,
    );
    const selectedPayable = eligiblePayables.find((payable) => payable.id === allocationPayableId);
    const submitAllocation = () => {
        if (!businessId || !selectedPayment || !selectedPayable || !globalThis.crypto?.randomUUID) {
            setAllocationError('پرداخت، فاکتور یا شناسه امن درخواست معتبر نیست.');
            return;
        }
        if (pendingAllocation) { allocationMutation.mutate(pendingAllocation); return; }
        const amount = allocationAmount.trim();
        const amountMinor = toMinor(amount);
        if (amountMinor <= 0n || amountMinor > toMinor(selectedPayment.remainingAmount)
            || amountMinor > toMinor(selectedPayable.outstandingAmount)) {
            setAllocationError('مبلغ باید بیشتر از صفر و حداکثر برابر مانده پرداخت و مانده فاکتور باشد.');
            return;
        }
        const input: CreatePaymentAllocationInput = {
            supplierPaymentId: selectedPayment.id,
            accountsPayableId: selectedPayable.id,
            amount: fromMinor(amountMinor),
        };
        const request: PendingAllocationRequest = {
            businessId: String(businessId), paymentId: selectedPayment.id,
            fingerprint: [businessId, selectedPayment.id, selectedPayable.id, fromMinor(amountMinor)].join(':'),
            key: globalThis.crypto.randomUUID(), input,
        };
        try { savePendingAllocation(request); }
        catch { setAllocationError('ذخیره شناسه امن تخصیص ناموفق بود؛ برای جلوگیری از ثبت تکراری درخواست ارسال نشد.'); return; }
        setPendingAllocation(request);
        allocationMutation.mutate(request);
    };

    const supplierNames = useMemo(
        () => new Map((suppliers.data ?? []).map((supplier) => [supplier.id, supplier.name])),
        [suppliers.data],
    );
    const totalAmount = useMemo(
        () => (payments.data ?? []).reduce((sum, payment) => sum + toMinor(payment.amount), 0n),
        [payments.data],
    );
    const resetFilters = () => { setSupplierFilter(''); setMethodFilter(''); setDateFrom(''); setDateTo(''); };
    const loading = (canView && payments.isLoading) || (canView && suppliers.isLoading);
    const pageError = payments.error ?? suppliers.error;
    const allocationDate = (value: string) => new Date(value).toLocaleString('fa-IR');

    return (
        <Container maxWidth="xl" dir="rtl" sx={{ py: 3 }}>
            <Stack spacing={2.5}>
                <Box>
                    <Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>پرداخت‌های تأمین‌کنندگان</Typography>
                    <Typography color="text.secondary">ثبت پرداخت، تخصیص به فاکتورهای بدهی و مشاهده تاریخچه تخصیص</Typography>
                </Box>
                {!canView && <Alert severity="warning">برای مشاهده تاریخچه پرداخت‌ها، مجوز purchase.view لازم است.</Alert>}
                {!canCreate && <Alert severity="info">برای ثبت پرداخت جدید، مجوز purchase.payment.create لازم است.</Alert>}
                {canCreate && !canView && <Alert severity="warning">برای انتخاب تأمین‌کننده و مشاهده تاریخچه، مجوز purchase.view نیز لازم است.</Alert>}
                {success && <Alert severity="success" onClose={() => setSuccess('')}>{success}</Alert>}
                {pageError && <Alert severity="error" action={<Button color="inherit" size="small" onClick={() => { void Promise.all([payments.refetch(), suppliers.refetch()]); }}>تلاش مجدد</Button>}>دریافت اطلاعات پرداخت ناموفق بود. {errorMessage(pageError)}</Alert>}

                {canView && <Card><CardContent>
                    <Typography color="text.secondary" variant="body2">جمع پرداخت‌های فهرست‌شده</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 700 }}>{money(fromMinor(totalAmount))}</Typography>
                </CardContent></Card>}

                {canCreate && canView && <Paper component="form" onSubmit={submit} sx={{ p: { xs: 1.5, sm: 2.5 } }}>
                    <Stack spacing={2}>
                        <Typography variant="h6">ثبت پرداخت جدید</Typography>
                        {pending && <Alert severity="warning" action={<Button color="inherit" size="small" disabled={paymentMutation.isPending} onClick={() => paymentMutation.mutate(pending)}>تلاش مجدد همان پرداخت</Button>}>یک پرداخت قبلی هنوز تعیین تکلیف نشده است؛ فقط همان درخواست با همان شناسه امن قابل ارسال مجدد است.</Alert>}
                        {formError && <Alert severity="error">{formError}</Alert>}
                        <TextField select required label="تأمین‌کننده" value={form.supplierId} disabled={Boolean(pending) || paymentMutation.isPending || suppliers.isLoading} onChange={(event) => setForm((current) => ({ ...current, supplierId: event.target.value }))}>
                            {(suppliers.data ?? []).filter((supplier) => supplier.isActive).map((supplier) => <MenuItem key={supplier.id} value={supplier.id}>{supplier.name}</MenuItem>)}
                        </TextField>
                        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                            <TextField required fullWidth label="مبلغ پرداخت" value={form.amount} disabled={Boolean(pending) || paymentMutation.isPending} onChange={(event) => setForm((current) => ({ ...current, amount: event.target.value }))} slotProps={{ htmlInput: { inputMode: 'decimal' } }} />
                            <TextField required fullWidth type="date" label="تاریخ پرداخت" value={form.paymentDate} disabled={Boolean(pending) || paymentMutation.isPending} onChange={(event) => setForm((current) => ({ ...current, paymentDate: event.target.value }))} slotProps={{ inputLabel: { shrink: true } }} />
                            <TextField select required fullWidth label="روش پرداخت" value={form.method} disabled={Boolean(pending) || paymentMutation.isPending} onChange={(event) => setForm((current) => ({ ...current, method: event.target.value as SupplierPaymentMethod }))}>
                                {Object.entries(methodLabels).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
                            </TextField>
                        </Stack>
                        <Button type="submit" variant="contained" disabled={!canCreate || !canView || paymentMutation.isPending || suppliers.isLoading || suppliers.isError}>
                            {paymentMutation.isPending ? <CircularProgress size={20} color="inherit" /> : pending ? 'ارسال مجدد همان پرداخت' : 'ثبت پرداخت'}
                        </Button>
                    </Stack>
                </Paper>}

                {canView && <>
                    <Typography variant="h6">تاریخچه پرداخت‌ها</Typography>
                    <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
                        <TextField select fullWidth label="تأمین‌کننده" value={supplierFilter} onChange={(event) => setSupplierFilter(event.target.value)}>
                            <MenuItem value="">همه تأمین‌کنندگان</MenuItem>
                            {(suppliers.data ?? []).map((supplier) => <MenuItem key={supplier.id} value={supplier.id}>{supplier.name}</MenuItem>)}
                        </TextField>
                        <TextField select fullWidth label="روش پرداخت" value={methodFilter} onChange={(event) => setMethodFilter(event.target.value)}>
                            <MenuItem value="">همه روش‌ها</MenuItem>
                            {Object.entries(methodLabels).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
                        </TextField>
                        <TextField fullWidth type="date" label="از تاریخ" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
                        <TextField fullWidth type="date" label="تا تاریخ" value={dateTo} onChange={(event) => setDateTo(event.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
                        <Button onClick={resetFilters}>پاک‌کردن</Button>
                    </Stack>
                    {payments.isLoading && <Box role="status" sx={{ display: 'flex', justifyContent: 'center', py: 5 }}><CircularProgress /></Box>}
                    {!payments.isLoading && !payments.isError && payments.data?.length === 0 && <Alert severity="info">پرداختی با فیلترهای انتخاب‌شده پیدا نشد.</Alert>}
                    {!!payments.data?.length && <Paper sx={{ overflowX: 'auto' }}>
                        <Table aria-label="تاریخچه پرداخت تأمین‌کنندگان">
                            <TableHead><TableRow>
                                <TableCell>شناسه</TableCell><TableCell>تأمین‌کننده</TableCell><TableCell>تاریخ</TableCell>
                                <TableCell>مبلغ</TableCell><TableCell>تخصیص‌یافته</TableCell><TableCell>مانده پرداخت</TableCell>
                                <TableCell>روش پرداخت</TableCell><TableCell>عملیات</TableCell>
                            </TableRow></TableHead>
                            <TableBody>{payments.data.map((payment) => <TableRow key={payment.id} hover>
                                <TableCell>#{payment.id}</TableCell>
                                <TableCell>{supplierNames.get(payment.supplierId) ?? `تأمین‌کننده #${payment.supplierId}`}</TableCell>
                                <TableCell>{dateLabel(payment.paymentDate)}</TableCell>
                                <TableCell>{money(payment.amount)}</TableCell>
                                <TableCell>{money(payment.allocatedAmount)}</TableCell>
                                <TableCell sx={{ fontWeight: 700 }}>{money(payment.remainingAmount)}</TableCell>
                                <TableCell>{methodLabels[payment.method]}</TableCell>
                                <TableCell><Button size="small" variant="outlined" disabled={!canAllocate || toMinor(payment.remainingAmount) <= 0n} onClick={() => openAllocation(payment.id)}>تخصیص / تاریخچه</Button></TableCell>
                            </TableRow>)}</TableBody>
                        </Table>
                    </Paper>}
                </>}
                {loading && <Box role="status" sx={{ display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>}
            </Stack>

            <Dialog open={Boolean(allocationPaymentId)} onClose={() => { if (!allocationMutation.isPending) setAllocationPaymentId(''); }} fullWidth maxWidth="md">
                <DialogTitle>تخصیص پرداخت به فاکتور</DialogTitle>
                <DialogContent dividers>
                    {!canAllocate && <Alert severity="warning">برای تخصیص پرداخت، مجوز purchase.payment.allocate لازم است.</Alert>}
                    {selectedPayment && <Stack spacing={1} sx={{ mb: 2 }}>
                        <Typography>پرداخت #{selectedPayment.id} — مبلغ: {money(selectedPayment.amount)}</Typography>
                        <Typography>تخصیص‌یافته: {money(selectedPayment.allocatedAmount)} | مانده قابل تخصیص: <strong>{money(selectedPayment.remainingAmount)}</strong></Typography>
                    </Stack>}
                    {payables.isLoading && <CircularProgress size={22} />}
                    {payables.isError && <Alert severity="error">{errorMessage(payables.error)}</Alert>}
                    {canAllocate && !pendingAllocation && <Stack spacing={2} sx={{ mb: 2 }}>
                        <TextField select fullWidth label="فاکتور پرداختنی" value={allocationPayableId} onChange={(event) => setAllocationPayableId(event.target.value)}>
                            {(eligiblePayables as AccountsPayable[]).map((payable) => <MenuItem key={payable.id} value={payable.id}>
                                {payable.invoiceNumber ?? `فاکتور #${payable.sourceInvoiceId}`} — مانده {money(payable.outstandingAmount)}
                            </MenuItem>)}
                        </TextField>
                        {selectedPayable && <Typography variant="body2" color="text.secondary">مانده این فاکتور: {money(selectedPayable.outstandingAmount)}</Typography>}
                        <TextField fullWidth label="مبلغ تخصیص" value={allocationAmount} onChange={(event) => setAllocationAmount(event.target.value)} slotProps={{ htmlInput: { inputMode: 'decimal' } }} />
                        {selectedPayment && <Typography variant="caption" color="text.secondary">حداکثر قابل تخصیص: {money(selectedPayment.remainingAmount)} (و حداکثر مانده فاکتور انتخاب‌شده)</Typography>}
                    </Stack>}
                    {pendingAllocation && <Alert severity="warning" action={<Button size="small" disabled={allocationMutation.isPending} onClick={() => allocationMutation.mutate(pendingAllocation)}>ارسال مجدد همان تخصیص</Button>}>
                        یک تخصیص هنوز تعیین تکلیف نشده است. فقط همان درخواست با همان شناسه امن قابل تکرار است.
                    </Alert>}
                    {allocationError && <Alert severity="error" sx={{ mt: 1 }}>{allocationError}</Alert>}
                    <Typography variant="subtitle1" sx={{ mt: 2, mb: 1, fontWeight: 700 }}>تاریخچه تخصیص‌های این پرداخت</Typography>
                    {allocationHistory.isLoading && <CircularProgress size={22} />}
                    {allocationHistory.isError && <Alert severity="error">{errorMessage(allocationHistory.error)}</Alert>}
                    {!allocationHistory.isLoading && !allocationHistory.isError && allocationHistory.data?.length === 0 && <Alert severity="info">هنوز تخصیصی برای این پرداخت ثبت نشده است.</Alert>}
                    {!!allocationHistory.data?.length && <Paper sx={{ overflowX: 'auto' }}>
                        <Table size="small" aria-label="تاریخچه تخصیص پرداخت">
                            <TableHead><TableRow><TableCell>شناسه تخصیص</TableCell><TableCell>فاکتور پرداختنی</TableCell><TableCell>مبلغ</TableCell><TableCell>زمان ثبت</TableCell></TableRow></TableHead>
                            <TableBody>{allocationHistory.data.map((allocation) => <TableRow key={allocation.id}>
                                <TableCell>#{allocation.id}</TableCell><TableCell>#{allocation.accountsPayableId}</TableCell>
                                <TableCell>{money(allocation.amount)}</TableCell><TableCell>{allocationDate(allocation.allocatedAt)}</TableCell>
                            </TableRow>)}</TableBody>
                        </Table>
                    </Paper>}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setAllocationPaymentId('')} disabled={allocationMutation.isPending}>بستن</Button>
                    {canAllocate && !pendingAllocation && <Button variant="contained" onClick={submitAllocation} disabled={allocationMutation.isPending || payables.isLoading || !selectedPayable || !allocationAmount.trim()}>
                        {allocationMutation.isPending ? <CircularProgress size={18} color="inherit" /> : 'ثبت تخصیص'}
                    </Button>}
                </DialogActions>
            </Dialog>
        </Container>
    );
};
