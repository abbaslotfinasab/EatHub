import { useMemo, useRef, useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Alert, Box, Button, CircularProgress, Container, MenuItem, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import { IngredientRepositoryImpl } from '../../../data/repositories/IngredientRepositoryImpl.ts';
import { WarehouseRepositoryImpl } from '../../../data/repositories/WarehouseRepositoryImpl.ts';
import { createOrderGoodsReceipt, getReceivingOrder, listOrderGoodsReceipts, listPurchaseSuppliers } from '../../../data/di/purchaseReceiving.ts';
import type { CreateGoodsReceiptInput } from '../../../domain/entities/inventory/facture/PurchaseReceiving.ts';
import { useAuthStore } from '../../store/auth.store.ts';

const ingredientRepository = new IngredientRepositoryImpl();
const warehouseRepository = new WarehouseRepositoryImpl();
const PAGE_SIZE = 100;

const normalizeDigits = (value: string): string => value
    .replace(/[۰-۹]/g, (digit) => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(digit)))
    .replace(/[٠-٩]/g, (digit) => String('٠١٢٣٤٥٦٧٨٩'.indexOf(digit)))
    .replace(/[٫٬]/g, (separator) => separator === '٫' ? '.' : '');

const toMilli = (value: string): bigint | null => {
    const match = /^(\d+)(?:\.(\d{1,3}))?$/.exec(normalizeDigits(value.trim()));
    if (!match) return null;
    return BigInt(match[1]) * 1000n + BigInt((match[2] ?? '').padEnd(3, '0'));
};

const fromMilli = (value: bigint): string => `${value / 1000n}.${String(value % 1000n).padStart(3, '0')}`;

const errorMessage = (error: unknown): string => {
    const response = (error as { response?: { status?: number; data?: unknown } })?.response;
    if (response?.status === 403) return 'مجوز لازم برای این عملیات را ندارید.';
    if (response?.status === 404) return 'سفارش یا یکی از منابع آن در کسب‌وکار جاری پیدا نشد.';
    if (response?.status === 409) return 'شناسه تکرار درخواست با اطلاعات دیگری استفاده شده است؛ صفحه را تازه‌سازی و وضعیت دریافت را بررسی کنید.';
    if (response?.status === 400 && response.data) {
        const flatten = (value: unknown): string[] => {
            if (typeof value === 'string') return [value];
            if (Array.isArray(value)) return value.flatMap(flatten);
            if (value && typeof value === 'object') return Object.values(value).flatMap(flatten);
            return [];
        };
        const details = flatten(response.data);
        if (details.length) return details.join(' ');
        return 'اطلاعات دریافت معتبر نیست؛ مقدار، واحد و سفارش را بررسی کنید.';
    }
    return 'ثبت دریافت انجام نشد. اتصال را بررسی کنید؛ برای تلاش مجدد، مقادیر را تغییر ندهید.';
};

type RequestIdentity = { fingerprint: string; key: string; receivedDate: string };

const getKey = (fingerprint: string, identities: Map<string, RequestIdentity>): RequestIdentity => {
    const current = identities.get(fingerprint);
    if (current) return current;
    if (!globalThis.crypto?.randomUUID) throw new Error('ساخت شناسه امن برای درخواست ممکن نیست.');
    const created = { fingerprint, key: globalThis.crypto.randomUUID(), receivedDate: new Date().toISOString() };
    identities.set(fingerprint, created);
    return created;
};

export const GoodsReceivingPage = () => {
    const { id = '' } = useParams();
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    const permissions = useAuthStore((state) => state.me?.active_business?.permissions ?? []);
    const canViewPurchase = permissions.includes('purchase.view');
    const canReceive = permissions.includes('purchase.receipt.create');
    const canViewInventory = permissions.includes('inventory.view');
    const [warehouseId, setWarehouseId] = useState('');
    const [notes, setNotes] = useState('');
    const [quantities, setQuantities] = useState<Record<string, string>>({});
    const [success, setSuccess] = useState('');
    const [formError, setFormError] = useState('');
    const idempotency = useRef(new Map<string, RequestIdentity>());

    const order = useQuery({
        queryKey: ['purchase-orders', userId, businessId, id],
        queryFn: () => getReceivingOrder.execute(id),
        enabled: Boolean(canViewPurchase && userId !== null && businessId !== null && id),
    });
    const receipts = useQuery({
        queryKey: ['goods-receipts', userId, businessId, id],
        queryFn: () => listOrderGoodsReceipts.execute(id),
        enabled: Boolean(canViewPurchase && userId !== null && businessId !== null && id && order.data),
    });
    const suppliers = useQuery({
        queryKey: ['purchase-suppliers', userId, businessId],
        queryFn: () => listPurchaseSuppliers.execute(),
        enabled: Boolean(canViewPurchase && userId !== null && businessId !== null),
    });
    const ingredients = useQuery({
        queryKey: ['purchase-receiving-ingredients', userId, businessId, id, order.data?.items.map((item) => item.ingredientId)],
        queryFn: () => ingredientRepository.findByIds([...new Set((order.data?.items ?? []).map((item) => item.ingredientId))]),
        enabled: Boolean(canViewInventory && order.data?.items.length),
    });
    const warehouses = useQuery({
        queryKey: ['purchase-receiving-warehouses', userId, businessId],
        queryFn: async () => {
            const first = await warehouseRepository.list({ page: 1, pageSize: PAGE_SIZE, isActive: true });
            const pages = Math.ceil(first.count / PAGE_SIZE);
            const remaining = await Promise.all(Array.from({ length: Math.max(0, pages - 1) }, (_, index) =>
                warehouseRepository.list({ page: index + 2, pageSize: PAGE_SIZE, isActive: true }),
            ));
            return [...first.results, ...remaining.flatMap((page) => page.results)];
        },
        enabled: Boolean(canViewInventory && userId !== null && businessId !== null),
    });

    const selectedWarehouseId = (warehouses.data?.some((warehouse) => warehouse.id === warehouseId) ? warehouseId : '')
        || warehouses.data?.find((warehouse) => warehouse.isDefault)?.id
        || warehouses.data?.[0]?.id
        || '';

    const previouslyReceived = useMemo(() => {
        const totals = new Map<string, bigint>();
        for (const receipt of receipts.data ?? []) {
            for (const line of receipt.items) {
                const quantity = toMilli(line.receivedQuantity);
                if (quantity === null) continue;
                totals.set(line.purchaseOrderItemId, (totals.get(line.purchaseOrderItemId) ?? 0n) + quantity);
            }
        }
        return totals;
    }, [receipts.data]);
    const ingredientById = new Map((ingredients.data ?? []).map((ingredient) => [ingredient.id, ingredient]));
    const supplierName = suppliers.data?.find((supplier) => supplier.id === order.data?.supplierId)?.name;
    const eligible = order.data?.status === 'sent' || order.data?.status === 'partial';
    const dataReady = Boolean(order.data && receipts.data && ingredients.data && warehouses.data && warehouses.data.length && canViewInventory);

    const receive = useMutation({
        mutationFn: (input: CreateGoodsReceiptInput) => createOrderGoodsReceipt.execute(input),
        onSuccess: async (receipt) => {
            idempotency.current.clear();
            setQuantities({});
            setSuccess(`دریافت شماره ${receipt.id} ثبت شد و موجودی از طریق گردش انبار به‌روزرسانی شد.`);
            await Promise.all([
                queryClient.invalidateQueries({ queryKey: ['purchase-orders', userId, businessId] }),
                queryClient.invalidateQueries({ queryKey: ['goods-receipts', userId, businessId, id] }),
                queryClient.invalidateQueries({ queryKey: ['inventory-stock-balances', userId, businessId] }),
                queryClient.invalidateQueries({ queryKey: ['inventory-movement-history', userId, businessId] }),
            ]);
        },
    });

    const submit = (event: FormEvent) => {
        event.preventDefault();
        setSuccess('');
        setFormError('');
        if (!order.data || !eligible || !canReceive || !dataReady || !selectedWarehouseId) return;
        const items: CreateGoodsReceiptInput['items'] = [];
        const quantityErrors: string[] = [];
        for (const line of order.data.items) {
            const text = quantities[line.id]?.trim() ?? '';
            if (!text || /^0+(?:\.0{1,3})?$/.test(text)) continue;
            const actual = toMilli(text);
            const ordered = toMilli(line.orderedQuantity);
            const received = previouslyReceived.get(line.id) ?? 0n;
            if (actual === null || actual <= 0n) {
                quantityErrors.push(`مقدار ردیف ${line.id} باید عددی مثبت با حداکثر سه رقم اعشار باشد.`);
                continue;
            }
            if (ordered === null || actual > ordered - received) {
                quantityErrors.push(`مقدار ردیف ${line.id} از مقدار باقی‌مانده بیشتر است.`);
                continue;
            }
            if (!line.purchaseUnit) {
                quantityErrors.push(`واحد خرید ردیف ${line.id} مشخص نیست و دریافت آن ممکن نیست.`);
                continue;
            }
            items.push({ purchaseOrderItemId: line.id, receivedQuantity: fromMilli(actual), purchaseUnit: line.purchaseUnit });
        }
        if (quantityErrors.length) {
            setFormError(quantityErrors.join(' '));
            return;
        }
        if (!items.length) {
            setFormError('برای ثبت دریافت، مقدار مثبت حداقل یک ردیف را وارد کنید.');
            return;
        }
        const fingerprint = JSON.stringify({
            businessId,
            purchaseOrderId: id,
            warehouseId: selectedWarehouseId,
            notes: notes.trim(),
            items: [...items].sort((a, b) => a.purchaseOrderItemId.localeCompare(b.purchaseOrderItemId)),
        });
        let requestIdentity: RequestIdentity;
        try {
            requestIdentity = getKey(fingerprint, idempotency.current);
        } catch (error) {
            setFormError(error instanceof Error ? error.message : 'ساخت شناسه درخواست ناموفق بود.');
            return;
        }
        receive.mutate({
            idempotencyKey: requestIdentity.key,
            purchaseOrderId: id,
            receivedDate: requestIdentity.receivedDate,
            notes: notes.trim(),
            warehouseId: selectedWarehouseId,
            items,
        });
    };

    const loading = order.isLoading || receipts.isLoading || suppliers.isLoading || (canViewInventory && (ingredients.isLoading || warehouses.isLoading));
    const error = order.error ?? receipts.error ?? suppliers.error ?? (canViewInventory ? ingredients.error ?? warehouses.error : null);
    const retryFailedQueries = () => {
        const retries: Promise<unknown>[] = [];
        if (order.isError) retries.push(order.refetch());
        if (receipts.isError) retries.push(receipts.refetch());
        if (suppliers.isError) retries.push(suppliers.refetch());
        if (canViewInventory && ingredients.isError) retries.push(ingredients.refetch());
        if (canViewInventory && warehouses.isError) retries.push(warehouses.refetch());
        void Promise.all(retries);
    };

    return (
        <Container maxWidth="lg" dir="rtl" sx={{ py: 3 }}>
            <Stack spacing={2.5}>
                <Stack direction={{ xs: 'column', sm: 'row' }} sx={{ justifyContent: 'space-between', alignItems: { sm: 'center' }, gap: 1 }}>
                    <Box>
                        <Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>ثبت دریافت کالا</Typography>
                        <Typography color="text.secondary">مقدار واقعی تحویل‌شده را برای هر ردیف سفارش ثبت کنید.</Typography>
                    </Box>
                    <Button onClick={() => navigate('/purchase/orders')}>بازگشت به سفارش‌ها</Button>
                </Stack>
                {!canViewPurchase && <Alert severity="error">برای مشاهده اطلاعات سفارش، مجوز خرید لازم است.</Alert>}
                {canViewPurchase && !canReceive && <Alert severity="warning">شما مجوز مشاهده سفارش را دارید، اما مجوز ثبت دریافت کالا ندارید.</Alert>}
                {canReceive && !canViewInventory && <Alert severity="error">برای انتخاب انبار و مشاهده اقلام، مجوز مشاهده موجودی لازم است.</Alert>}
                {loading && <Box role="status" sx={{ display: 'flex', justifyContent: 'center', py: 5 }}><CircularProgress /></Box>}
                {error && <Alert severity="error" action={<Button color="inherit" size="small" onClick={retryFailedQueries}>تلاش مجدد</Button>}>{errorMessage(error)}</Alert>}
                {success && <Alert severity={receive.isError ? 'error' : 'success'} onClose={() => setSuccess('')}>{success}</Alert>}
                {formError && <Alert severity="error" onClose={() => setFormError('')}>{formError}</Alert>}
                {order.data && <>
                    <Paper sx={{ p: 2.5 }}>
                        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                            <Typography><strong>سفارش:</strong> #{order.data.id}</Typography>
                            <Typography><strong>تأمین‌کننده:</strong> {supplierName ?? `شناسه ${order.data.supplierId}`}</Typography>
                            <Typography><strong>وضعیت:</strong> {order.data.status === 'partial' ? 'دریافت جزئی' : order.data.status === 'sent' ? 'ارسال‌شده' : order.data.status}</Typography>
                        </Stack>
                    </Paper>
                    {!eligible && <Alert severity="info">ثبت دریافت فقط برای سفارش‌های ارسال‌شده یا دارای دریافت جزئی ممکن است.</Alert>}
                    {eligible && !order.data.items.length && <Alert severity="warning">این سفارش ردیف قابل دریافتی ندارد.</Alert>}
                    {receipts.data?.length ? <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" sx={{ mb: 1 }}>سوابق دریافت</Typography>
                        <Stack spacing={1}>{receipts.data.map((receipt) => <Box key={receipt.id} sx={{ borderBottom: '1px solid', borderColor: 'divider', pb: 1 }}>
                            <Typography variant="body2">دریافت #{receipt.id} — {new Date(receipt.receivedDate).toLocaleString('fa-IR')} — انبار {receipt.warehouseId ?? 'پیش‌فرض'}</Typography>
                            <Typography variant="body2" color="text.secondary">{receipt.items.map((line) => `ردیف ${line.purchaseOrderItemId}: ${line.receivedQuantity} ${line.purchaseUnit ?? ''}`).join('، ')}</Typography>
                        </Box>)}</Stack>
                    </Paper> : receipts.data && <Alert severity="info">هنوز دریافتی برای این سفارش ثبت نشده است.</Alert>}
                    {eligible && !!order.data.items.length && <Paper component="form" onSubmit={submit} sx={{ p: { xs: 1.5, sm: 2.5 } }}>
                        <Stack spacing={2}>
                            <Typography variant="h6">مقادیر واقعی دریافت</Typography>
                            <Alert severity="info">ثبت این فرم بلافاصله مقدار پذیرفته‌شده را از طریق گردش موجودی به انبار اضافه می‌کند. ردیف خالی یا صفر در درخواست ارسال نمی‌شود.</Alert>
                            {!warehouses.data?.length && warehouses.isSuccess && <Alert severity="warning">انبار فعالی برای این کسب‌وکار وجود ندارد؛ ابتدا یک انبار فعال ثبت کنید.</Alert>}
                            <TextField select required label="انبار مقصد" value={selectedWarehouseId} onChange={(event) => setWarehouseId(event.target.value)} disabled={!warehouses.data?.length || receive.isPending}>
                                {(warehouses.data ?? []).map((warehouse) => <MenuItem key={warehouse.id} value={warehouse.id}>{warehouse.name}{warehouse.isDefault ? ' (پیش‌فرض)' : ''}</MenuItem>)}
                            </TextField>
                            <Box sx={{ overflowX: 'auto' }}><Table size="small" aria-label="اقلام سفارش برای دریافت">
                                <TableHead><TableRow><TableCell>قلم</TableCell><TableCell>مقدار سفارش</TableCell><TableCell>قبلاً دریافت‌شده</TableCell><TableCell>باقی‌مانده</TableCell><TableCell>دریافت فعلی</TableCell></TableRow></TableHead>
                                <TableBody>{order.data.items.map((line) => {
                                    const ordered = toMilli(line.orderedQuantity) ?? 0n;
                                    const received = previouslyReceived.get(line.id) ?? 0n;
                                    const remaining = ordered > received ? ordered - received : 0n;
                                    const ingredient = ingredientById.get(line.ingredientId);
                                    return <TableRow key={line.id}>
                                        <TableCell>{ingredient?.name ?? `ماده ${line.ingredientId}`}<Typography variant="caption" sx={{ display: 'block' }} color="text.secondary">ردیف #{line.id}</Typography></TableCell>
                                        <TableCell>{line.orderedQuantity} {line.purchaseUnit ?? '—'}</TableCell>
                                        <TableCell>{fromMilli(received)} {line.purchaseUnit ?? ''}</TableCell>
                                        <TableCell>{fromMilli(remaining)} {line.purchaseUnit ?? ''}</TableCell>
                                        <TableCell sx={{ minWidth: 170 }}><TextField size="small" fullWidth value={quantities[line.id] ?? ''} onChange={(event) => setQuantities((current) => ({ ...current, [line.id]: event.target.value }))} placeholder="۰" disabled={receive.isPending || !line.purchaseUnit || remaining === 0n} slotProps={{ htmlInput: { inputMode: 'decimal', 'aria-label': `مقدار دریافت ردیف ${line.id}` } }} helperText={line.purchaseUnit ? `حداکثر ${fromMilli(remaining)} ${line.purchaseUnit}` : 'واحد خرید مشخص نیست'} /></TableCell>
                                    </TableRow>;
                                })}</TableBody>
                            </Table></Box>
                            <TextField label="توضیحات (اختیاری)" multiline minRows={2} value={notes} onChange={(event) => setNotes(event.target.value)} disabled={receive.isPending} />
                            {receive.isError && <Alert severity="error">{errorMessage(receive.error)}</Alert>}
                            <Stack direction="row" spacing={1}>
                                <Button type="submit" variant="contained" disabled={!canReceive || !dataReady || !selectedWarehouseId || receive.isPending || !eligible}>
                                    {receive.isPending ? <CircularProgress size={20} color="inherit" /> : 'ثبت دریافت انتخاب‌شده'}
                                </Button>
                                <Button type="button" onClick={() => navigate('/purchase/orders')} disabled={receive.isPending}>انصراف</Button>
                            </Stack>
                        </Stack>
                    </Paper>}
                </>}
            </Stack>
        </Container>
    );
};
