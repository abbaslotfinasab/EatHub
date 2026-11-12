import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
    Alert, Box, Button, Card, CardContent, CircularProgress, Container, MenuItem,
    Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography,
} from '@mui/material';
import { listPurchaseSuppliersManagement } from '../../../data/di/purchaseSupplier.ts';
import { createSupplierPayment, listSupplierPayments } from '../../../data/di/supplierPayment.ts';
import type {
    CreateSupplierPaymentInput,
    SupplierPaymentFilters,
    SupplierPaymentMethod,
} from '../../../domain/entities/inventory/SupplierPayment.ts';
import type { PurchaseSupplier } from '../../../domain/entities/inventory/PurchaseSupplier.ts';
import { useAuthStore } from '../../store/auth.store.ts';
import {
    clearSupplierPaymentRequestIdentity,
    getOrCreateSupplierPaymentRequestIdentity,
    listSupplierPaymentRequestIdentities,
} from '../../utils/supplierPaymentRequestIdentity.ts';

const methodLabels: Record<SupplierPaymentMethod, string> = {
    cash: 'نقدی',
    bank_transfer: 'انتقال بانکی',
    card: 'کارت',
    cheque: 'چک',
    credit: 'اعتباری',
    other: 'سایر',
};
const money = (value: string) => Number(value || 0).toLocaleString('fa-IR', { maximumFractionDigits: 2 });
const localDate = () => {
    const now = new Date();
    return [now.getFullYear(), String(now.getMonth() + 1).padStart(2, '0'), String(now.getDate()).padStart(2, '0')].join('-');
};
const normalizeDigits = (value: string) => value
    .replace(/[۰-۹]/g, (digit) => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(digit)))
    .replace(/[٠-٩]/g, (digit) => String('٠١٢٣٤٥٦٧٨٩'.indexOf(digit)))
    .replace(/[٫٬]/g, (separator) => separator === '٫' ? '.' : '');
const normalizeAmount = (value: string): string | null => {
    const normalized = normalizeDigits(value.trim());
    if (!/^\\d+(?:\\.\\d{1,2})?$/.test(normalized)) return null;
    const [whole, fraction = ''] = normalized.split('.');
    const cents = BigInt(whole) * 100n + BigInt(fraction.padEnd(2, '0'));
    if (cents <= 0n) return null;
    return `${cents / 100n}.${String(cents % 100n).padStart(2, '0')}`;
};
const flattenError = (value: unknown): string[] => {
    if (typeof value === 'string') return [value];
    if (Array.isArray(value)) return value.flatMap(flattenError);
    if (value && typeof value === 'object') return Object.values(value).flatMap(flattenError);
    return [];
};
const errorMessage = (error: unknown) => {
    const response = (error as { response?: { status?: number; data?: unknown } })?.response;
    if (response?.status === 403) return 'مجوز ثبت یا مشاهده پرداخت تأمین‌کننده را ندارید.';
    if (response?.status === 404) return 'تأمین‌کننده در کسب‌وکار جاری پیدا نشد.';
    if (response?.status === 400 && response.data) {
        const details = flattenError(response.data);
        return details.length ? details.join(' ') : 'اطلاعات پرداخت معتبر نیست.';
    }
    return 'پاسخ قطعی از سرور دریافت نشد. برای جلوگیری از پرداخت تکراری، همان درخواست با همان شناسه قابل تلاش مجدد است.';
};

type PendingPaymentRequest = { fingerprint: string; input: CreateSupplierPaymentInput };

const parsePendingRequest = (fingerprint: string, key: string): PendingPaymentRequest | null => {
    try {
        const payload = JSON.parse(fingerprint) as {
            businessId?: number;
            supplierId?: string;
            amount?: string;
            paymentDate?: string;
            method?: SupplierPaymentMethod;
        };
        if (
            !Number.isInteger(payload.businessId)
            || typeof payload.supplierId !== 'string'
            || typeof payload.amount !== 'string'
            || typeof payload.paymentDate !== 'string'
            || !payload.method
        ) return null;
        return {
            fingerprint,
            input: {
                supplierId: payload.supplierId,
                amount: payload.amount,
                paymentDate: payload.paymentDate,
                method: payload.method,
                idempotencyKey: key,
            },
        };
    } catch {
        return null;
    }
};

export const SupplierPaymentsPage = () => {
    const queryClient = useQueryClient();
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    const permissions = useAuthStore((state) => state.me?.active_business?.permissions ?? []);
    const canView = permissions.includes('purchase.view');
    const canCreate = permissions.includes('purchase.payment.create');
    const canViewSuppliers = canView || permissions.includes('purchase.supplier.manage');

    const [supplierId, setSupplierId] = useState('');
    const [methodFilter, setMethodFilter] = useState('all');
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');
    const [formSupplierId, setFormSupplierId] = useState('');
    const [amount, setAmount] = useState('');
    const [paymentDate, setPaymentDate] = useState(localDate);
    const [paymentMethod, setPaymentMethod] = useState<SupplierPaymentMethod>('bank_transfer');
    const [pendingRequest, setPendingRequest] = useState<PendingPaymentRequest | null>(null);
    const [formError, setFormError] = useState('');
    const [success, setSuccess] = useState('');

    const filters = useMemo<SupplierPaymentFilters>(() => ({
        ...(supplierId ? { supplierId } : {}),
        ...(methodFilter === 'all' ? {} : { method: methodFilter as SupplierPaymentMethod }),
        ...(dateFrom ? { paymentDateFrom: dateFrom } : {}),
        ...(dateTo ? { paymentDateTo: dateTo } : {}),
    }), [supplierId, methodFilter, dateFrom, dateTo]);

    const payments = useQuery({
        queryKey: ['supplier-payments', userId, businessId, filters],
        queryFn: () => listSupplierPayments.execute(filters),
        enabled: Boolean(canView && userId !== null && businessId !== null),
    });
    const suppliers = useQuery({
        queryKey: ['purchase-suppliers', userId, businessId, 'supplier-payment-form'],
        queryFn: () => listPurchaseSuppliersManagement.execute({ isActive: true }),
        enabled: Boolean(canViewSuppliers && userId !== null && businessId !== null),
    });

    const supplierById = useMemo(
        () => new Map((suppliers.data ?? []).map((supplier: PurchaseSupplier) => [supplier.id, supplier])),
        [suppliers.data],
    );

    useEffect(() => {
        if (!businessId) {
            setPendingRequest(null);
            return;
        }
        try {
            const identities = listSupplierPaymentRequestIdentities(window.sessionStorage);
            const pending = identities
                .map((identity) => parsePendingRequest(identity.fingerprint, identity.key))
                .find((candidate) => {
                    if (!candidate) return false;
                    try {
                        const payload = JSON.parse(candidate.fingerprint) as { businessId?: number };
                        return String(payload.businessId) === String(businessId);
                    } catch {
                        return false;
                    }
                });
            setPendingRequest(pending ?? null);
            if (pending) {
                setFormSupplierId(pending.input.supplierId);
                setAmount(pending.input.amount);
                setPaymentDate(pending.input.paymentDate);
                setPaymentMethod(pending.input.method);
            }
        } catch {
            setPendingRequest(null);
        }
    }, [businessId]);

    const refresh = async () => {
        await queryClient.invalidateQueries({ queryKey: ['supplier-payments', userId, businessId] });
    };

    const createMutation = useMutation({
        mutationFn: (request: PendingPaymentRequest) => createSupplierPayment.execute(request.input),
        onSuccess: async (payment, request) => {
            try { clearSupplierPaymentRequestIdentity(request.fingerprint, window.sessionStorage); } catch { /* server success remains authoritative */ }
            setPendingRequest(null);
            setFormError('');
            setSuccess(`پرداخت شماره ${payment.id} با موفقیت ثبت شد.`);
            setAmount('');
            await refresh();
        },
        onError: (error, request) => {
            const status = (error as { response?: { status?: number } })?.response?.status ?? 0;
            if ([400, 403, 404].includes(status)) {
                try { clearSupplierPaymentRequestIdentity(request.fingerprint, window.sessionStorage); } catch { /* keep original error visible */ }
                setPendingRequest(null);
            }
            setFormError(errorMessage(error));
        },
    });

    const submit = (event: FormEvent) => {
        event.preventDefault();
        setFormError('');
        setSuccess('');
        if (pendingRequest) {
            setFormError('یک درخواست قبلی هنوز تعیین تکلیف نشده است. ابتدا همان درخواست را دوباره ارسال کنید.');
            return;
        }
        const normalizedAmount = normalizeAmount(amount);
        if (!canCreate || !businessId || !formSupplierId || !normalizedAmount || !paymentDate) {
            setFormError('تأمین‌کننده، مبلغ مثبت و تاریخ پرداخت را کامل و معتبر وارد کنید.');
            return;
        }
        if (!globalThis.crypto?.randomUUID) {
            setFormError('مرورگر امکان ساخت شناسه امن درخواست را فراهم نمی‌کند.');
            return;
        }
        const fingerprint = JSON.stringify({
            businessId,
            supplierId: formSupplierId,
            amount: normalizedAmount,
            paymentDate,
            method: paymentMethod,
        });
        try {
            const identity = getOrCreateSupplierPaymentRequestIdentity(
                fingerprint,
                window.sessionStorage,
                () => globalThis.crypto.randomUUID(),
            );
            const request = parsePendingRequest(fingerprint, identity.key);
            if (!request) throw new Error('اطلاعات درخواست ذخیره‌شده معتبر نیست.');
            setPendingRequest(request);
            createMutation.mutate(request);
        } catch (error) {
            setFormError(error instanceof Error ? error.message : 'ذخیره امن شناسه درخواست ناموفق بود.');
        }
    };

    const resetFilters = () => {
        setSupplierId('');
        setMethodFilter('all');
        setDateFrom('');
        setDateTo('');
    };
    const methodLabel = (value: SupplierPaymentMethod) => methodLabels[value] ?? value;

    return (
        <Container maxWidth="xl" dir="rtl" sx={{ py: 3 }}>
            <Stack spacing={2.5}>
                <Box>
                    <Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>پرداخت‌های تأمین‌کنندگان</Typography>
                    <Typography color="text.secondary">ثبت و پیگیری پرداخت‌ها؛ تخصیص به فاکتورها در مرحله بعد انجام می‌شود.</Typography>
                </Box>

                {!canView && <Alert severity="warning">برای مشاهده فهرست پرداخت‌ها، مجوز مشاهده خرید لازم است.</Alert>}
                {!canCreate && <Alert severity="info">شما مجوز مشاهده پرداخت‌ها را دارید، اما مجوز ثبت پرداخت جدید را ندارید.</Alert>}
                {payments.isError && <Alert severity="error" action={<Button color="inherit" size="small" onClick={() => { void payments.refetch(); }}>تلاش مجدد</Button>}>دریافت پرداخت‌ها ناموفق بود: {errorMessage(payments.error)}</Alert>}
                {suppliers.isError && <Alert severity="error" action={<Button color="inherit" size="small" onClick={() => { void suppliers.refetch(); }}>تلاش مجدد</Button>}>دریافت فهرست تأمین‌کنندگان ناموفق بود.</Alert>}
                {success && <Alert severity="success" onClose={() => setSuccess('')}>{success}</Alert>}

                {pendingRequest && <Alert severity="warning" action={<Button color="inherit" size="small" disabled={createMutation.isPending} onClick={() => createMutation.mutate(pendingRequest)}>تلاش مجدد همان درخواست</Button>}>
                    یک پرداخت قبلی هنوز پاسخ قطعی نگرفته است. برای جلوگیری از ثبت دوباره، همان payload با همان کلید idempotency ارسال می‌شود.
                </Alert>}

                {canCreate && <Paper component="form" onSubmit={submit} sx={{ p: { xs: 1.5, sm: 2.5 } }}>
                    <Stack spacing={2}>
                        <Typography variant="h6">ثبت پرداخت جدید</Typography>
                        <Alert severity="info">این مرحله فقط پرداخت را ثبت می‌کند؛ تخصیص آن به یک یا چند فاکتور در P5.3 اضافه می‌شود.</Alert>
                        {formError && <Alert severity="error" onClose={() => setFormError('')}>{formError}</Alert>}
                        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
                            <TextField select required fullWidth label="تأمین‌کننده" value={formSupplierId} onChange={(event) => setFormSupplierId(event.target.value)} disabled={createMutation.isPending || Boolean(pendingRequest) || suppliers.isLoading}>
                                {(suppliers.data ?? []).map((supplier) => <MenuItem key={supplier.id} value={supplier.id}>{supplier.name}</MenuItem>)}
                            </TextField>
                            <TextField required fullWidth label="مبلغ پرداخت" value={amount} onChange={(event) => setAmount(event.target.value)} disabled={createMutation.isPending || Boolean(pendingRequest)} slotProps={{ htmlInput: { inputMode: 'decimal' } }} />
                            <TextField required type="date" fullWidth label="تاریخ پرداخت" value={paymentDate} onChange={(event) => setPaymentDate(event.target.value)} disabled={createMutation.isPending || Boolean(pendingRequest)} slotProps={{ inputLabel: { shrink: true } }} />
                            <TextField select required fullWidth label="روش پرداخت" value={paymentMethod} onChange={(event) => setPaymentMethod(event.target.value as SupplierPaymentMethod)} disabled={createMutation.isPending || Boolean(pendingRequest)}>
                                {Object.entries(methodLabels).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
                            </TextField>
                        </Stack>
                        <Button type="submit" variant="contained" disabled={!canCreate || createMutation.isPending || Boolean(pendingRequest) || suppliers.isLoading || !suppliers.data?.length}>
                            {createMutation.isPending ? <CircularProgress size={20} color="inherit" /> : 'ثبت پرداخت'}
                        </Button>
                    </Stack>
                </Paper>}

                {canView && <>
                    <Paper sx={{ p: 2 }}>
                        <Stack spacing={1.5}>
                            <Typography variant="h6">فیلتر پرداخت‌ها</Typography>
                            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
                                <TextField select fullWidth label="تأمین‌کننده" value={supplierId} onChange={(event) => setSupplierId(event.target.value)}>
                                    <MenuItem value="">همه تأمین‌کنندگان</MenuItem>
                                    {(suppliers.data ?? []).map((supplier) => <MenuItem key={supplier.id} value={supplier.id}>{supplier.name}</MenuItem>)}
                                </TextField>
                                <TextField select fullWidth label="روش پرداخت" value={methodFilter} onChange={(event) => setMethodFilter(event.target.value)}>
                                    <MenuItem value="all">همه روش‌ها</MenuItem>
                                    {Object.entries(methodLabels).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
                                </TextField>
                                <TextField type="date" fullWidth label="از تاریخ" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
                                <TextField type="date" fullWidth label="تا تاریخ" value={dateTo} onChange={(event) => setDateTo(event.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
                                <Button onClick={resetFilters}>پاک‌کردن</Button>
                            </Stack>
                        </Stack>
                    </Paper>
                    {payments.isLoading && <Box role="status" sx={{ display: 'flex', justifyContent: 'center', py: 5 }}><CircularProgress /></Box>}
                    {!payments.isLoading && !payments.isError && payments.data?.length === 0 && <Alert severity="info">پرداختی با این فیلترها پیدا نشد.</Alert>}
                    {!!payments.data?.length && <Paper sx={{ overflowX: 'auto' }}>
                        <Table aria-label="فهرست پرداخت‌های تأمین‌کنندگان">
                            <TableHead><TableRow>
                                <TableCell>شناسه پرداخت</TableCell><TableCell>تأمین‌کننده</TableCell><TableCell>تاریخ</TableCell><TableCell>روش</TableCell><TableCell>مبلغ</TableCell>
                            </TableRow></TableHead>
                            <TableBody>{payments.data.map((payment) => {
                                const supplier = supplierById.get(payment.supplierId);
                                return <TableRow key={payment.id} hover>
                                    <TableCell>#{payment.id}</TableCell>
                                    <TableCell>{supplier?.name ?? `تأمین‌کننده #${payment.supplierId}`}</TableCell>
                                    <TableCell>{new Date(`${payment.paymentDate}T00:00:00`).toLocaleDateString('fa-IR')}</TableCell>
                                    <TableCell>{methodLabel(payment.method)}</TableCell>
                                    <TableCell sx={{ fontWeight: 700 }}>{money(payment.amount)}</TableCell>
                                </TableRow>;
                            })}</TableBody>
                        </Table>
                    </Paper>}
                </>}
            </Stack>
        </Container>
    );
};
