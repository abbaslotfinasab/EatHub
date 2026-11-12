import { useMemo, useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
    Alert, Box, Button, CircularProgress, Container, Dialog, DialogActions, DialogContent,
    DialogTitle, MenuItem, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow,
    TextField, Typography,
} from '@mui/material';
import {
    approvePurchaseInvoice, cancelPurchaseInvoice, createPurchaseInvoice, getPurchaseInvoice,
    listPurchaseInvoices, matchPurchaseInvoice, postPurchaseInvoice, updatePurchaseInvoice,
    listPurchaseInvoiceEvents,
} from '../../../data/di/purchaseInvoice.ts';
import { listReceivingOrders } from '../../../data/di/purchaseReceiving.ts';
import { listPurchaseSuppliersManagement } from '../../../data/di/purchaseSupplier.ts';
import type { PurchaseInvoice, PurchaseInvoiceInput, PurchaseInvoiceItemInput } from '../../../domain/entities/inventory/PurchaseInvoice.ts';
import { useAuthStore } from '../../store/auth.store.ts';

type InvoiceFormLine = PurchaseInvoiceItemInput;
type InvoiceForm = PurchaseInvoiceInput;

const emptyForm: InvoiceForm = {
    supplierId: '', purchaseOrderId: '', invoiceNumber: '', invoiceDate: new Date().toISOString().slice(0, 10),
    discountPercent: '0', taxPercent: '0', items: [],
};
const errorMessage = (error: unknown) => {
    const response = (error as { response?: { status?: number; data?: unknown } })?.response;
    if (response?.status === 403) return 'مجوز لازم برای این عملیات را ندارید.';
    if (response?.data) return JSON.stringify(response.data);
    return error instanceof Error ? error.message : 'عملیات ناموفق بود؛ دوباره تلاش کنید.';
};
const statusLabel: Record<string, string> = {
    draft: 'پیش‌نویس', approved: 'تأییدشده', posted: 'ثبت مالی‌شده', cancelled: 'لغوشده',
};
const matchLabel: Record<string, string> = {
    not_matched: 'تطبیق‌نشده', pending_receipt: 'در انتظار دریافت', matched: 'منطبق', exception: 'دارای مغایرت',
};
const money = (value: string) => Number(value || 0).toLocaleString('fa-IR', { maximumFractionDigits: 2 });
const quantity = (value: string) => Number(value || 0).toLocaleString('fa-IR', { maximumFractionDigits: 3 });

export const PurchaseInvoicesPage = () => {
    const queryClient = useQueryClient();
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    const permissions = useAuthStore((state) => state.me?.active_business?.permissions ?? []);
    const canView = permissions.includes('purchase.view');
    const canCreate = permissions.includes('purchase.invoice.create');
    const canUpdate = permissions.includes('purchase.invoice.update');
    const canApprove = permissions.includes('purchase.invoice.approve');
    const canMatch = permissions.includes('purchase.invoice.match');
    const canPost = permissions.includes('purchase.invoice.post');
    const canCancel = permissions.includes('purchase.invoice.cancel');

    const [supplierFilter, setSupplierFilter] = useState('');
    const [orderFilter, setOrderFilter] = useState('');
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [selectedId, setSelectedId] = useState('');
    const [formOpen, setFormOpen] = useState(false);
    const [editing, setEditing] = useState<PurchaseInvoice | null>(null);
    const [form, setForm] = useState<InvoiceForm>(emptyForm);
    const [formError, setFormError] = useState('');
    const [actionError, setActionError] = useState('');
    const [cancelOpen, setCancelOpen] = useState(false);
    const [cancelReason, setCancelReason] = useState('');
    const [dueDate, setDueDate] = useState('');

    const filters = useMemo(() => ({
        supplierId: supplierFilter || undefined,
        purchaseOrderId: orderFilter || undefined,
        dateFrom: dateFrom || undefined,
        dateTo: dateTo || undefined,
    }), [supplierFilter, orderFilter, dateFrom, dateTo]);

    const invoices = useQuery({
        queryKey: ['purchase-invoices', userId, businessId, filters],
        queryFn: () => listPurchaseInvoices.execute(filters),
        enabled: Boolean(canView && userId && businessId),
    });
    const orders = useQuery({
        queryKey: ['purchase-orders', userId, businessId],
        queryFn: () => listReceivingOrders.execute(),
        enabled: Boolean(canView && userId && businessId),
    });
    const suppliers = useQuery({
        queryKey: ['purchase-supplier-management', userId, businessId, 'invoice-options'],
        queryFn: () => listPurchaseSuppliersManagement.execute(),
        enabled: Boolean(canView && userId && businessId),
    });
    const detail = useQuery({
        queryKey: ['purchase-invoice', userId, businessId, selectedId],
        queryFn: () => getPurchaseInvoice.execute(selectedId),
        enabled: Boolean(selectedId && canView && userId && businessId),
    });
    const auditEvents = useQuery({
        queryKey: ['purchase-invoice-events', userId, businessId, selectedId],
        queryFn: () => listPurchaseInvoiceEvents.execute(selectedId),
        enabled: Boolean(selectedId && canView && detail.data && userId && businessId),
        retry: false,
    });
    const matchPreview = useQuery({
        queryKey: ['purchase-invoice-match', userId, businessId, selectedId],
        queryFn: () => matchPurchaseInvoice.execute(selectedId, false),
        enabled: Boolean(selectedId && canView && detail.data && ['approved', 'posted'].includes(detail.data.status)),
        retry: false,
    });

    const refresh = async (id?: string) => {
        await Promise.all([
            queryClient.invalidateQueries({ queryKey: ['purchase-invoices', userId, businessId] }),
            ...(id ? [
                queryClient.invalidateQueries({ queryKey: ['purchase-invoice', userId, businessId, id] }),
                queryClient.invalidateQueries({ queryKey: ['purchase-invoice-match', userId, businessId, id] }),
                queryClient.invalidateQueries({ queryKey: ['purchase-invoice-events', userId, businessId, id] }),
            ] : []),
            queryClient.invalidateQueries({ queryKey: ['accounts-payables', userId, businessId] }),
        ]);
    };

    const closeForm = () => {
        setFormOpen(false); setEditing(null); setForm(emptyForm); setFormError('');
    };
    const openCreate = () => {
        setEditing(null); setForm(emptyForm); setFormError(''); setFormOpen(true);
    };
    const openEdit = (invoice: PurchaseInvoice) => {
        setEditing(invoice);
        setForm({
            supplierId: invoice.supplierId,
            purchaseOrderId: invoice.purchaseOrderId,
            invoiceNumber: invoice.invoiceNumber,
            invoiceDate: invoice.invoiceDate,
            discountPercent: invoice.discountPercent,
            taxPercent: invoice.taxPercent,
            items: invoice.items.map((item) => ({
                ingredientId: item.ingredientId,
                purchaseOrderItemId: item.purchaseOrderItemId,
                description: item.description,
                quantity: item.quantity,
                unitPrice: item.unitPrice,
                discountPercent: item.discountPercent,
                taxPercent: item.taxPercent,
            })),
        });
        setFormError(''); setFormOpen(true);
    };
    const selectOrder = (orderId: string) => {
        const order = orders.data?.find((item) => item.id === orderId);
        setForm((current) => ({
            ...current,
            purchaseOrderId: orderId,
            supplierId: order?.supplierId ?? '',
            items: order ? order.items.map((item) => ({
                ingredientId: item.ingredientId,
                purchaseOrderItemId: item.id,
                description: '',
                quantity: item.orderedQuantity,
                unitPrice: item.unitPrice,
                discountPercent: '0',
                taxPercent: '0',
            })) : [],
        }));
    };
    const updateLine = (index: number, key: keyof InvoiceFormLine, value: string) => {
        setForm((current) => ({
            ...current,
            items: current.items.map((item, itemIndex) => itemIndex === index ? { ...item, [key]: value } : item),
        }));
    };

    const createMutation = useMutation({
        mutationFn: (input: InvoiceForm) => createPurchaseInvoice.execute(input),
        onSuccess: async (invoice) => { await refresh(); closeForm(); setSelectedId(invoice.id); },
        onError: (error) => setFormError(errorMessage(error)),
    });
    const updateMutation = useMutation({
        mutationFn: ({ id, input }: { id: string; input: InvoiceForm }) => updatePurchaseInvoice.execute(id, input),
        onSuccess: async (invoice) => { await refresh(invoice.id); closeForm(); },
        onError: (error) => setFormError(errorMessage(error)),
    });
    const actionMutation = useMutation({
        mutationFn: async ({ action, id, reason, due }: { action: 'approve' | 'match' | 'post' | 'cancel'; id: string; reason?: string; due?: string }) => {
            if (action === 'approve') return approvePurchaseInvoice.execute(id);
            if (action === 'match') { await matchPurchaseInvoice.execute(id, true); return getPurchaseInvoice.execute(id); }
            if (action === 'post') return postPurchaseInvoice.execute(id, due);
            return cancelPurchaseInvoice.execute(id, reason ?? '');
        },
        onSuccess: async (invoice) => { await refresh(invoice.id); setActionError(''); setCancelOpen(false); setCancelReason(''); },
        onError: (error) => setActionError(errorMessage(error)),
    });

    const submitForm = (event: FormEvent) => {
        event.preventDefault(); setFormError('');
        if (editing) updateMutation.mutate({ id: editing.id, input: form });
        else createMutation.mutate(form);
    };
    const saving = createMutation.isPending || updateMutation.isPending;
    const visibleInvoices = (invoices.data ?? []).filter((invoice) => statusFilter === 'all' || invoice.status === statusFilter);
    const supplierName = (id: string) => suppliers.data?.find((supplier) => supplier.id === id)?.name ?? `تأمین‌کننده #${id}`;
    const orderName = (id: string) => {
        const order = orders.data?.find((item) => item.id === id);
        return order ? `سفارش #${id} — ${supplierName(order.supplierId)}` : `سفارش #${id}`;
    };
    const selectedOrder = orders.data?.find((order) => order.id === form.purchaseOrderId);
    const selectedMatch = matchPreview.data?.current;
    const canPostNow = detail.data?.status === 'approved' && selectedMatch?.status === 'matched';

    return (
        <Container maxWidth="xl" dir="rtl" sx={{ py: 3 }}>
            <Stack spacing={2.5}>
                <Stack direction={{ xs: 'column', sm: 'row' }} sx={{ justifyContent: 'space-between', alignItems: { sm: 'center' }, gap: 1 }}>
                    <Box>
                        <Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>فاکتورهای خرید</Typography>
                        <Typography color="text.secondary">ثبت فاکتور، تطبیق با سفارش و دریافت، و ثبت بدهی تأمین‌کننده</Typography>
                    </Box>
                    {canCreate && <Button variant="contained" onClick={openCreate}>ثبت فاکتور خرید</Button>}
                </Stack>
                {!canView && <Alert severity="error">برای مشاهده فاکتورهای خرید، مجوز مشاهده خرید لازم است.</Alert>}
                {invoices.isError && <Alert severity="error" action={<Button color="inherit" onClick={() => { void invoices.refetch(); }}>تلاش مجدد</Button>}>دریافت فاکتورها ناموفق بود. {errorMessage(invoices.error)}</Alert>}
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
                    <TextField select fullWidth label="تأمین‌کننده" value={supplierFilter} onChange={(event) => setSupplierFilter(event.target.value)}>
                        <MenuItem value="">همه تأمین‌کنندگان</MenuItem>
                        {(suppliers.data ?? []).map((supplier) => <MenuItem key={supplier.id} value={supplier.id}>{supplier.name}</MenuItem>)}
                    </TextField>
                    <TextField select fullWidth label="سفارش خرید" value={orderFilter} onChange={(event) => setOrderFilter(event.target.value)}>
                        <MenuItem value="">همه سفارش‌ها</MenuItem>
                        {(orders.data ?? []).map((order) => <MenuItem key={order.id} value={order.id}>#{order.id} — {supplierName(order.supplierId)}</MenuItem>)}
                    </TextField>
                    <TextField type="date" label="از تاریخ" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
                    <TextField type="date" label="تا تاریخ" value={dateTo} onChange={(event) => setDateTo(event.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
                    <TextField select label="وضعیت" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} sx={{ minWidth: 150 }}>
                        <MenuItem value="all">همه وضعیت‌ها</MenuItem>
                        <MenuItem value="draft">پیش‌نویس</MenuItem><MenuItem value="approved">تأییدشده</MenuItem>
                        <MenuItem value="posted">ثبت مالی‌شده</MenuItem><MenuItem value="cancelled">لغوشده</MenuItem>
                    </TextField>
                </Stack>
                {invoices.isLoading && <Box role="status" sx={{ display: 'flex', justifyContent: 'center', py: 5 }}><CircularProgress /></Box>}
                {!invoices.isLoading && !invoices.isError && visibleInvoices.length === 0 && <Alert severity="info">فاکتوری با این فیلترها پیدا نشد.</Alert>}
                {!!visibleInvoices.length && <Paper sx={{ overflowX: 'auto' }}>
                    <Table aria-label="فهرست فاکتورهای خرید">
                        <TableHead><TableRow>
                            <TableCell>شماره فاکتور</TableCell><TableCell>تأمین‌کننده</TableCell><TableCell>سفارش</TableCell>
                            <TableCell>تاریخ</TableCell><TableCell>مبلغ نهایی</TableCell><TableCell>وضعیت</TableCell>
                            <TableCell>وضعیت تطبیق</TableCell><TableCell>جزئیات</TableCell>
                        </TableRow></TableHead>
                        <TableBody>{visibleInvoices.map((invoice) => <TableRow key={invoice.id} hover>
                            <TableCell>{invoice.invoiceNumber}</TableCell><TableCell>{supplierName(invoice.supplierId)}</TableCell>
                            <TableCell>#{invoice.purchaseOrderId}</TableCell><TableCell>{invoice.invoiceDate}</TableCell>
                            <TableCell>{money(invoice.totalPrice)}</TableCell><TableCell>{statusLabel[invoice.status]}</TableCell>
                            <TableCell>{matchLabel[invoice.matchingStatus]}</TableCell>
                            <TableCell><Button size="small" onClick={() => { setSelectedId(invoice.id); setActionError(''); }}>مشاهده</Button></TableCell>
                        </TableRow>)}</TableBody>
                    </Table>
                </Paper>}
            </Stack>

            <Dialog open={formOpen} onClose={saving ? undefined : closeForm} fullWidth maxWidth="md">
                <DialogTitle>{editing ? 'ویرایش پیش‌نویس فاکتور' : 'ثبت فاکتور خرید'}</DialogTitle>
                <Box component="form" onSubmit={submitForm}>
                    <DialogContent>
                        <Stack spacing={2} sx={{ pt: 1 }}>
                            {formError && <Alert severity="error">{formError}</Alert>}
                            <TextField select required label="سفارش خرید" value={form.purchaseOrderId} onChange={(event) => selectOrder(event.target.value)} disabled={saving || Boolean(editing)}>
                                {(orders.data ?? []).filter((order) => ['sent', 'partial', 'received'].includes(order.status)).map((order) => (
                                    <MenuItem key={order.id} value={order.id}>#{order.id} — {supplierName(order.supplierId)} — {order.status}</MenuItem>
                                ))}
                            </TextField>
                            <TextField label="تأمین‌کننده" value={form.supplierId ? supplierName(form.supplierId) : 'ابتدا سفارش را انتخاب کنید'} disabled />
                            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                                <TextField required fullWidth label="شماره فاکتور" value={form.invoiceNumber} onChange={(event) => setForm((current) => ({ ...current, invoiceNumber: event.target.value }))} disabled={saving} />
                                <TextField required fullWidth type="date" label="تاریخ فاکتور" value={form.invoiceDate} onChange={(event) => setForm((current) => ({ ...current, invoiceDate: event.target.value }))} slotProps={{ inputLabel: { shrink: true } }} disabled={saving} />
                            </Stack>
                            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                                <TextField fullWidth type="number" label="تخفیف کل (%)" value={form.discountPercent} onChange={(event) => setForm((current) => ({ ...current, discountPercent: event.target.value }))} slotProps={{ htmlInput: { min: 0, max: 100, step: '0.01' } }} disabled={saving} />
                                <TextField fullWidth type="number" label="مالیات کل (%)" value={form.taxPercent} onChange={(event) => setForm((current) => ({ ...current, taxPercent: event.target.value }))} slotProps={{ htmlInput: { min: 0, step: '0.01' } }} disabled={saving} />
                            </Stack>
                            <Typography sx={{ fontWeight: 700 }}>اقلام فاکتور</Typography>
                            {!form.items.length && <Alert severity="info">برای شروع، یک سفارش خرید معتبر انتخاب کنید.</Alert>}
                            {form.items.map((item, index) => {
                                const poItem = selectedOrder?.items.find((line) => line.id === item.purchaseOrderItemId);
                                return <Paper key={item.purchaseOrderItemId} variant="outlined" sx={{ p: 2 }}>
                                    <Stack spacing={1}>
                                        <Typography sx={{ fontWeight: 600 }}>قلم سفارش #{item.purchaseOrderItemId} — ماده اولیه #{item.ingredientId}{poItem ? ` (سفارش: ${quantity(poItem.orderedQuantity)} ${poItem.purchaseUnit ?? ''})` : ''}</Typography>
                                        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
                                            <TextField fullWidth type="number" label="مقدار فاکتور" value={item.quantity} onChange={(event) => updateLine(index, 'quantity', event.target.value)} slotProps={{ htmlInput: { min: 0.001, step: 0.001 } }} disabled={saving} />
                                            <TextField fullWidth type="number" label="قیمت واحد" value={item.unitPrice} onChange={(event) => updateLine(index, 'unitPrice', event.target.value)} slotProps={{ htmlInput: { min: 0, step: 0.01 } }} disabled={saving} />
                                            <TextField fullWidth type="number" label="تخفیف قلم (%)" value={item.discountPercent} onChange={(event) => updateLine(index, 'discountPercent', event.target.value)} slotProps={{ htmlInput: { min: 0, max: 100, step: 0.01 } }} disabled={saving} />
                                            <TextField fullWidth type="number" label="مالیات قلم (%)" value={item.taxPercent} onChange={(event) => updateLine(index, 'taxPercent', event.target.value)} slotProps={{ htmlInput: { min: 0, step: 0.01 } }} disabled={saving} />
                                        </Stack>
                                        <TextField fullWidth label="شرح قلم (اختیاری)" value={item.description} onChange={(event) => updateLine(index, 'description', event.target.value)} disabled={saving} />
                                    </Stack>
                                </Paper>;
                            })}
                        </Stack>
                    </DialogContent>
                    <DialogActions sx={{ px: 3, pb: 2 }}>
                        <Button onClick={closeForm} disabled={saving}>انصراف</Button>
                        <Button type="submit" variant="contained" disabled={saving || !form.purchaseOrderId || !form.items.length || !form.invoiceNumber.trim()}>
                            {saving ? <CircularProgress size={20} color="inherit" /> : editing ? 'ذخیره تغییرات' : 'ثبت پیش‌نویس'}
                        </Button>
                    </DialogActions>
                </Box>
            </Dialog>

            <Dialog open={Boolean(selectedId)} onClose={() => setSelectedId('')} fullWidth maxWidth="lg">
                <DialogTitle>جزئیات فاکتور خرید</DialogTitle>
                <DialogContent>
                    {detail.isLoading && <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}><CircularProgress /></Box>}
                    {detail.isError && <Alert severity="error">{errorMessage(detail.error)}</Alert>}
                    {actionError && <Alert severity="error" sx={{ mb: 2 }}>{actionError}</Alert>}
                    {detail.data && <Stack spacing={2}>
                        <Stack direction={{ xs: 'column', sm: 'row' }} sx={{ justifyContent: 'space-between', gap: 1 }}>
                            <Box>
                                <Typography variant="h6">{detail.data.invoiceNumber}</Typography>
                                <Typography color="text.secondary">{supplierName(detail.data.supplierId)} · {orderName(detail.data.purchaseOrderId)} · {detail.data.invoiceDate}</Typography>
                            </Box>
                            <Box>
                                <Typography>وضعیت: {statusLabel[detail.data.status]}</Typography>
                                <Typography>تطبیق ثبت‌شده: {matchLabel[detail.data.matchingStatus]}</Typography>
                            </Box>
                        </Stack>
                        <Paper variant="outlined" sx={{ p: 2 }}>
                            <Typography sx={{ fontWeight: 700, mb: 1 }}>اقلام</Typography>
                            {detail.data.items.map((item) => <Stack key={item.id} direction="row" sx={{ justifyContent: 'space-between', gap: 2, py: 0.5 }}>
                                <Typography>قلم سفارش #{item.purchaseOrderItemId} · مقدار {quantity(item.quantity)} · قیمت واحد {money(item.unitPrice)}</Typography>
                                <Typography>{money(item.totalPrice)}</Typography>
                            </Stack>)}
                            <Typography sx={{ textAlign: "left", fontWeight: 700, mt: 1 }}>جمع کل: {money(detail.data.totalPrice)}</Typography>
                        </Paper>
                        <Paper variant="outlined" sx={{ p: 2 }}>
                            <Typography sx={{ fontWeight: 700 }}>گردش وضعیت موجود</Typography>
                            <Typography variant="body2">ایجاد: {detail.data.createdAt ?? '—'}</Typography>
                            <Typography variant="body2">تأیید: {detail.data.approvedAt ?? '—'} · کاربر #{detail.data.approvedById ?? '—'}</Typography>
                            <Typography variant="body2">آخرین تطبیق: {detail.data.matchedAt ?? '—'} · {matchLabel[detail.data.matchingStatus]}</Typography>
                            <Typography variant="body2">ثبت مالی: {detail.data.postedAt ?? '—'} · کاربر #{detail.data.postedById ?? '—'}</Typography>
                            {detail.data.cancelledAt && <Typography variant="body2">لغو: {detail.data.cancelledAt} · کاربر #{detail.data.cancelledById ?? '—'} · {detail.data.cancellationReason}</Typography>}
                            <Typography variant="caption" color="text.secondary">تاریخچه تغییرات و تطبیق‌های ثبت‌شده در بخش «تاریخچه رویدادها» نمایش داده می‌شود.</Typography>
                        </Paper>

                        <Paper variant="outlined" sx={{ p: 2 }}>
                            <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', gap: 1, mb: 1 }}>
                                <Typography sx={{ fontWeight: 700 }}>تاریخچه رویدادها</Typography>
                                <Button size="small" onClick={() => { void auditEvents.refetch(); }} disabled={auditEvents.isFetching}>بروزرسانی</Button>
                            </Stack>
                            {auditEvents.isLoading && <CircularProgress size={20} />}
                            {auditEvents.isError && <Alert severity="error" action={<Button color="inherit" onClick={() => { void auditEvents.refetch(); }}>تلاش مجدد</Button>}>دریافت تاریخچه ناموفق بود: {errorMessage(auditEvents.error)}</Alert>}
                            {!auditEvents.isLoading && !auditEvents.isError && !auditEvents.data?.length && <Typography variant="body2" color="text.secondary">رویدادی برای این فاکتور ثبت نشده است.</Typography>}
                            {(auditEvents.data ?? []).map((event) => {
                                const eventTitle: Record<string, string> = {
                                    created: 'ایجاد پیش‌نویس',
                                    updated: 'ویرایش فاکتور',
                                    approved: 'تأیید فاکتور',
                                    match_persisted: 'ثبت نتیجه تطبیق',
                                    posted: 'ثبت مالی و ایجاد بدهی',
                                    cancelled: 'لغو فاکتور',
                                };
                                return <Box key={event.id} sx={{ py: 1, borderBottom: 1, borderColor: 'divider', '&:last-child': { borderBottom: 0 } }}>
                                    <Stack direction={{ xs: 'column', sm: 'row' }} sx={{ justifyContent: 'space-between', gap: 0.5 }}>
                                        <Typography sx={{ fontWeight: 600 }}>{eventTitle[event.eventType] ?? event.eventType}</Typography>
                                        <Typography variant="caption" color="text.secondary">{new Date(event.occurredAt).toLocaleString('fa-IR')}</Typography>
                                    </Stack>
                                    <Typography variant="body2" color="text.secondary">
                                        کاربر: {event.actorName ?? (event.actorId ? '#' + event.actorId : 'نامشخص')}
                                        {event.previousStatus || event.resultingStatus ? ' · ' + (event.previousStatus ?? '—') + ' ← ' + (event.resultingStatus ?? '—') : ''}
                                    </Typography>
                                    {event.eventType === 'match_persisted' && typeof event.metadata.previous_matching_status === 'string' && (
                                        <Typography variant="caption" color="text.secondary">
                                            وضعیت تطبیق قبلی: {event.metadata.previous_matching_status}
                                        </Typography>
                                    )}
                                    {event.eventType === 'cancelled' && typeof event.metadata.reason === 'string' && (
                                        <Typography variant="body2">دلیل لغو: {event.metadata.reason}</Typography>
                                    )}
                                </Box>;
                            })}
                        </Paper>

                        {['approved', 'posted'].includes(detail.data.status) && <Paper variant="outlined" sx={{ p: 2 }}>
                            <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', gap: 1, mb: 1 }}>
                                <Typography sx={{ fontWeight: 700 }}>نتیجه تطبیق سه‌طرفه</Typography>
                                <Button size="small" onClick={() => { void matchPreview.refetch(); }} disabled={matchPreview.isFetching}>محاسبه مجدد</Button>
                            </Stack>
                            {matchPreview.isLoading && <CircularProgress size={20} />}
                            {matchPreview.isError && <Alert severity="error">{errorMessage(matchPreview.error)}</Alert>}
                            {matchPreview.data && <>
                                <Alert severity={selectedMatch?.status === 'matched' ? 'success' : 'warning'} sx={{ mb: 1 }}>
                                    وضعیت فعلی: {matchLabel[matchPreview.data.current.status]} · آخرین نتیجه ثبت‌شده: {matchLabel[matchPreview.data.lastPersisted.status]}
                                </Alert>
                                {matchPreview.data.current.exceptions.map((exception) => <Typography key={exception.code} color="error" variant="body2">{exception.code}: {exception.message}</Typography>)}
                                <Table size="small">
                                    <TableHead><TableRow>
                                        <TableCell>قلم PO</TableCell><TableCell>سفارش</TableCell><TableCell>دریافت سالم</TableCell>
                                        <TableCell>فاکتورهای قبلی</TableCell><TableCell>این فاکتور</TableCell><TableCell>مانده مجاز</TableCell>
                                        <TableCell>قیمت PO</TableCell><TableCell>قیمت فاکتور</TableCell><TableCell>اختلاف</TableCell>
                                    </TableRow></TableHead>
                                    <TableBody>{matchPreview.data.current.lines.map((line) => <TableRow key={line.invoiceItemId}>
                                        <TableCell>#{line.purchaseOrderItemId}</TableCell><TableCell>{quantity(line.orderedQuantity)}</TableCell>
                                        <TableCell>{quantity(line.acceptedReceivedQuantity)}</TableCell><TableCell>{quantity(line.previouslyInvoicedQuantity)}</TableCell>
                                        <TableCell>{quantity(line.currentInvoiceQuantity)}</TableCell><TableCell>{quantity(line.availableQuantity)}</TableCell>
                                        <TableCell>{money(line.purchaseOrderUnitPrice)}</TableCell><TableCell>{money(line.invoiceUnitPrice)}</TableCell>
                                        <TableCell>{money(line.priceVariance)}</TableCell>
                                    </TableRow>)}</TableBody>
                                </Table>
                                {matchPreview.data.current.lines.flatMap((line) => line.exceptions).map((exception, index) => <Typography key={`${exception.code}-${index}`} variant="caption" color="error">{exception.code}: {exception.message}</Typography>)}
                            </>}
                        </Paper>}
                    </Stack>}
                </DialogContent>
                <DialogActions sx={{ px: 3, pb: 2, flexWrap: 'wrap', gap: 1 }}>
                    {detail.data?.status === 'draft' && canUpdate && <Button onClick={() => openEdit(detail.data!)}>ویرایش</Button>}
                    {detail.data?.status === 'draft' && canApprove && <Button variant="contained" onClick={() => actionMutation.mutate({ action: 'approve', id: selectedId })} disabled={actionMutation.isPending}>تأیید فاکتور</Button>}
                    {detail.data?.status === 'approved' && canMatch && <Button variant="outlined" onClick={() => actionMutation.mutate({ action: 'match', id: selectedId })} disabled={actionMutation.isPending}>ثبت نتیجه تطبیق</Button>}
                    {detail.data?.status === 'approved' && canPost && <TextField size="small" type="date" label="سررسید بدهی" value={dueDate} onChange={(event) => setDueDate(event.target.value)} slotProps={{ inputLabel: { shrink: true } }} />}
                    {detail.data?.status === 'approved' && canPost && <Button variant="contained" color="success" onClick={() => actionMutation.mutate({ action: 'post', id: selectedId, due: dueDate || undefined })} disabled={actionMutation.isPending || !canPostNow}>ثبت مالی و ایجاد بدهی</Button>}
                    {['draft', 'approved'].includes(detail.data?.status ?? '') && canCancel && <Button color="error" onClick={() => setCancelOpen(true)} disabled={actionMutation.isPending}>لغو فاکتور</Button>}
                    <Button onClick={() => setSelectedId('')}>بستن</Button>
                </DialogActions>
            </Dialog>

            <Dialog open={cancelOpen} onClose={() => setCancelOpen(false)} fullWidth maxWidth="xs">
                <DialogTitle>لغو فاکتور</DialogTitle>
                <DialogContent><TextField fullWidth multiline minRows={3} label="دلیل لغو" value={cancelReason} onChange={(event) => setCancelReason(event.target.value)} sx={{ mt: 1 }} /></DialogContent>
                <DialogActions>
                    <Button onClick={() => setCancelOpen(false)}>انصراف</Button>
                    <Button color="error" variant="contained" disabled={!cancelReason.trim() || actionMutation.isPending} onClick={() => actionMutation.mutate({ action: 'cancel', id: selectedId, reason: cancelReason })}>ثبت لغو</Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};
