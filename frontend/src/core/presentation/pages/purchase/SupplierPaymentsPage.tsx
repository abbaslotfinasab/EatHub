import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
    Alert, Box, Button, Card, CardContent, CircularProgress, Container, MenuItem,
    Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography,
} from '@mui/material';
import { createSupplierPayment, listSupplierPayments } from '../../../data/di/supplierPayment.ts';
import { listPurchaseSuppliersManagement } from '../../../data/di/purchaseSupplier.ts';
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

const methodLabels: Record<SupplierPaymentMethod, string> = {
    cash: 'نقدی',
    bank_transfer: 'انتقال بانکی',
    card: 'کارت',
    cheque: 'چک',
    credit: 'اعتباری',
    other: 'سایر',
};
const emptyForm: CreateSupplierPaymentInput = {
    supplierId: '',
    amount: '',
    paymentDate: '',
    method: 'bank_transfer',
};
const money = (value: string) => Number(value || 0).toLocaleString('fa-IR', { maximumFractionDigits: 2 });
const dateLabel = (value: string) => new Date(`${value}T00:00:00`).toLocaleDateString('fa-IR');
const errorMessage = (error: unknown) => {
    const response = (error as { response?: { status?: number; data?: unknown } })?.response;
    if (response?.status === 403) return 'مجوز ثبت پرداخت تأمین‌کننده را ندارید.';
    if (response?.status === 404) return 'تأمین‌کننده در کسب‌وکار جاری پیدا نشد.';
    if (response?.status === 409) return 'این شناسه درخواست با اطلاعات دیگری استفاده شده است؛ اطلاعات پرداخت را بررسی کنید.';
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
    return 'نتیجه ثبت پرداخت مشخص نیست. برای جلوگیری از پرداخت تکراری، همان درخواست را با همان اطلاعات دوباره ارسال کنید.';
};

export const SupplierPaymentsPage = () => {
    const queryClient = useQueryClient();
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    const permissions = useAuthStore((state) => state.me?.active_business?.permissions ?? []);
    const canView = permissions.includes('purchase.view');
    const canCreate = permissions.includes('purchase.payment.create');

    const [supplierFilter, setSupplierFilter] = useState('');
    const [methodFilter, setMethodFilter] = useState('');
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');
    const [form, setForm] = useState<CreateSupplierPaymentInput>(emptyForm);
    const [pending, setPending] = useState<PendingSupplierPaymentRequest | null>(null);
    const [formError, setFormError] = useState('');
    const [success, setSuccess] = useState('');

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

    useEffect(() => {
        if (!businessId) {
            setPending(null);
            return;
        }
        try {
            const restored = readPendingSupplierPayment(String(businessId), window.sessionStorage);
            if (restored) {
                setPending(restored);
                setForm(restored.input);
            }
        } catch {
            setFormError('فضای ذخیره امن درخواست در این مرورگر در دسترس نیست؛ برای جلوگیری از ثبت تکراری، پرداخت ارسال نشد.');
        }
    }, [businessId]);

    const refresh = async () => {
        await Promise.all([
            queryClient.invalidateQueries({ queryKey: ['supplier-payments', userId, businessId] }),
            queryClient.invalidateQueries({ queryKey: ['accounts-payables', userId, businessId] }),
        ]);
    };

    const paymentMutation = useMutation({
        mutationFn: (request: PendingSupplierPaymentRequest) =>
            createSupplierPayment.execute(request.input, request.key),
        onSuccess: async (payment, request) => {
            try { clearPendingSupplierPayment(request.businessId, window.sessionStorage); } catch { /* server success is authoritative */ }
            setPending(null);
            setForm(emptyForm);
            setFormError('');
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

    const submit = (event: FormEvent) => {
        event.preventDefault();
        setFormError('');
        setSuccess('');
        if (!businessId || !canCreate) return;
        if (pending) {
            paymentMutation.mutate(pending);
            return;
        }
        const input: CreateSupplierPaymentInput = {
            supplierId: form.supplierId,
            amount: form.amount.trim(),
            paymentDate: form.paymentDate,
            method: form.method,
        };
        const fingerprint = supplierPaymentFingerprint(String(businessId), input);
        if (!globalThis.crypto?.randomUUID) {
            setFormError('ساخت شناسه امن پرداخت در این مرورگر ممکن نیست.');
            return;
        }
        const request: PendingSupplierPaymentRequest = {
            businessId: String(businessId),
            fingerprint,
            key: globalThis.crypto.randomUUID(),
            input,
        };
        try {
            savePendingSupplierPayment(request, window.sessionStorage);
        } catch {
            setFormError('ذخیره شناسه امن پرداخت ناموفق بود؛ برای جلوگیری از ثبت تکراری، درخواست ارسال نشد.');
            return;
        }
        setPending(request);
        paymentMutation.mutate(request);
    };

    const supplierNames = useMemo(
        () => new Map((suppliers.data ?? []).map((supplier) => [supplier.id, supplier.name])),
        [suppliers.data],
    );
    const totalAmount = useMemo(
        () => (payments.data ?? []).reduce((sum, payment) => sum + Number(payment.amount), 0),
        [payments.data],
    );

    const resetFilters = () => {
        setSupplierFilter('');
        setMethodFilter('');
        setDateFrom('');
        setDateTo('');
    };
    const loading = (canView && payments.isLoading) || (canView && suppliers.isLoading);
    const pageError = payments.error ?? suppliers.error;

    return (
        <Container maxWidth="xl" dir="rtl" sx={{ py: 3 }}>
            <Stack spacing={2.5}>
                <Box>
                    <Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>پرداخت‌های تأمین‌کنندگان</Typography>
                    <Typography color="text.secondary">ثبت و مشاهده پرداخت‌های مستقل از تخصیص به فاکتور</Typography>
                </Box>

                {!canView && <Alert severity="warning">برای مشاهده تاریخچه پرداخت‌ها، مجوز purchase.view لازم است.</Alert>}
                {!canCreate && <Alert severity="info">برای ثبت پرداخت جدید، مجوز purchase.payment.create لازم است.</Alert>}
                {canCreate && !canView && <Alert severity="warning">برای انتخاب تأمین‌کننده و مشاهده تاریخچه، مجوز purchase.view نیز لازم است. تا زمان دریافت این مجوز، فرم ثبت پرداخت در دسترس نیست.</Alert>}
                {success && <Alert severity="success" onClose={() => setSuccess('')}>{success}</Alert>}
                {pageError && <Alert severity="error" action={<Button color="inherit" size="small" onClick={() => { void Promise.all([payments.refetch(), suppliers.refetch()]); }}>تلاش مجدد</Button>}>
                    دریافت اطلاعات پرداخت ناموفق بود. {errorMessage(pageError)}
                </Alert>}

                {canView && <Card><CardContent>
                    <Typography color="text.secondary" variant="body2">جمع پرداخت‌های فهرست‌شده</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 700 }}>{money(String(totalAmount))}</Typography>
                </CardContent></Card>}

                {canCreate && canView && <Paper component="form" onSubmit={submit} sx={{ p: { xs: 1.5, sm: 2.5 } }}>
                    <Stack spacing={2}>
                        <Typography variant="h6">ثبت پرداخت جدید</Typography>
                        {pending && <Alert severity="warning" action={<Button color="inherit" size="small" disabled={paymentMutation.isPending} onClick={() => paymentMutation.mutate(pending)}>تلاش مجدد همان پرداخت</Button>}>
                            یک پرداخت قبلی هنوز تعیین تکلیف نشده است. اطلاعات قفل شده و فقط همان درخواست با همان شناسه امن قابل ارسال مجدد است.
                        </Alert>}
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
                        <Alert severity="info">این مرحله فقط پرداخت را ثبت می‌کند؛ تخصیص آن به فاکتور و محاسبه تسویه در P5.3 انجام می‌شود.</Alert>
                        <Stack direction="row" spacing={1}>
                            <Button type="submit" variant="contained" disabled={!canCreate || !canView || paymentMutation.isPending || suppliers.isLoading || suppliers.isError}>
                                {paymentMutation.isPending ? <CircularProgress size={20} color="inherit" /> : pending ? 'ارسال مجدد همان پرداخت' : 'ثبت پرداخت'}
                            </Button>
                        </Stack>
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
                                <TableCell>شناسه</TableCell><TableCell>تأمین‌کننده</TableCell><TableCell>تاریخ</TableCell><TableCell>مبلغ</TableCell><TableCell>روش پرداخت</TableCell>
                            </TableRow></TableHead>
                            <TableBody>{payments.data.map((payment) => <TableRow key={payment.id} hover>
                                <TableCell>#{payment.id}</TableCell>
                                <TableCell>{supplierNames.get(payment.supplierId) ?? `تأمین‌کننده #${payment.supplierId}`}</TableCell>
                                <TableCell>{dateLabel(payment.paymentDate)}</TableCell>
                                <TableCell>{money(payment.amount)}</TableCell>
                                <TableCell>{methodLabels[payment.method]}</TableCell>
                            </TableRow>)}</TableBody>
                        </Table>
                    </Paper>}
                </>}
                {loading && <Box role="status" sx={{ display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>}
            </Stack>
        </Container>
    );
};
