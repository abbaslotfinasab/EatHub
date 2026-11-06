import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Alert, Box, Button, CircularProgress, Container, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import { IngredientRepositoryImpl } from '../../../data/repositories/IngredientRepositoryImpl.ts';
import {
    createPurchaseOrder,
    getReceivingOrder,
    listPurchaseSuppliers,
    updatePurchaseOrder,
} from '../../../data/di/purchaseReceiving.ts';
import type { PurchaseUnit } from '../../../domain/entities/inventory/facture/PurchaseReceiving.ts';
import { useAuthStore } from '../../store/auth.store.ts';

type DraftLine = { key: string; ingredientId: string; quantity: string; unitPrice: string; purchaseUnit: PurchaseUnit };
const units: { value: PurchaseUnit; label: string }[] = [
    { value: 'kg', label: 'کیلوگرم' },
    { value: 'g', label: 'گرم' },
    { value: 'l', label: 'لیتر' },
    { value: 'ml', label: 'میلی‌لیتر' },
    { value: 'pc', label: 'عدد' },
];
const today = () => {
    const date = new Date();
    const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
    return local.toISOString().slice(0, 10);
};
const errorMessage = (error: unknown) => {
    const response = (error as { response?: { status?: number; data?: unknown } })?.response;
    if (response?.status === 403) return 'مجوز لازم برای این عملیات را ندارید.';
    if (response?.data) return JSON.stringify(response.data);
    return error instanceof Error ? error.message : 'ثبت سفارش ناموفق بود؛ اتصال را بررسی کنید.';
};
const newLine = (): DraftLine => ({
    key: globalThis.crypto?.randomUUID?.() ?? String(Date.now() + Math.random()),
    ingredientId: '',
    quantity: '1',
    unitPrice: '0',
    purchaseUnit: 'kg',
});

export const CreatePurchaseOrderPage = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    const permissions = useAuthStore((state) => state.me?.active_business?.permissions ?? []);
    const canCreate = permissions.includes('purchase.order.create');
    const canUpdate = permissions.includes('purchase.order.update');
    const ingredientRepository = useMemo(() => new IngredientRepositoryImpl(), []);
    const order = useQuery({
        queryKey: ['purchase-orders', userId, businessId, id],
        queryFn: () => getReceivingOrder.execute(id!),
        enabled: Boolean(id && userId && businessId && canUpdate),
    });
    const suppliers = useQuery({
        queryKey: ['purchase-suppliers', userId, businessId],
        queryFn: () => listPurchaseSuppliers.execute(),
        enabled: Boolean(userId && businessId && (canCreate || canUpdate)),
    });
    const ingredients = useQuery({
        queryKey: ['purchase-order-ingredients', userId, businessId],
        queryFn: async () => {
            const first = await ingredientRepository.findAll({ page: 1, pageSize: 100, isActive: true });
            const pages = Math.ceil(first.count / 100);
            const rest = await Promise.all(Array.from({ length: Math.max(0, pages - 1) }, (_, index) =>
                ingredientRepository.findAll({ page: index + 2, pageSize: 100, isActive: true }),
            ));
            return [...first.results, ...rest.flatMap((page) => page.results)];
        },
        enabled: Boolean(userId && businessId && (canCreate || canUpdate)),
    });

    const [supplierId, setSupplierId] = useState('');
    const [orderDate, setOrderDate] = useState(today);
    const [expectedDate, setExpectedDate] = useState('');
    const [discount, setDiscount] = useState('0');
    const [tax, setTax] = useState('0');
    const [lines, setLines] = useState<DraftLine[]>([newLine()]);
    const [formError, setFormError] = useState('');
    const isEdit = Boolean(id);

    useEffect(() => {
        if (!order.data) return;
        setSupplierId(order.data.supplierId);
        setOrderDate(order.data.orderDate);
        setExpectedDate(order.data.expectedDate ?? '');
        setDiscount(order.data.discount);
        setTax(order.data.tax);
        setLines(order.data.items.map((item) => ({
            key: item.id,
            ingredientId: item.ingredientId,
            quantity: item.orderedQuantity,
            unitPrice: item.unitPrice,
            purchaseUnit: item.purchaseUnit ?? 'kg',
        })));
    }, [order.data]);

    const mutation = useMutation({
        mutationFn: async () => {
            const items = lines.map((line) => ({
                ingredientId: line.ingredientId,
                quantity: line.quantity.trim(),
                unitPrice: line.unitPrice.trim(),
                purchaseUnit: line.purchaseUnit,
            }));
            if (items.some((item) => !item.ingredientId || !/^\d+(?:\.\d{1,3})?$/.test(item.quantity) || Number(item.quantity) <= 0 || !/^\d+(?:\.\d{1,2})?$/.test(item.unitPrice) || Number(item.unitPrice) < 0)) {
                throw new Error('قلم‌ها باید ماده اولیه، مقدار مثبت (حداکثر سه رقم اعشار) و قیمت معتبر داشته باشند.');
            }
            if (!supplierId) throw new Error('انتخاب تأمین‌کننده الزامی است.');
            if (!/^\d+(?:\.\d{1,2})?$/.test(discount) || !/^\d+(?:\.\d{1,2})?$/.test(tax)) {
                throw new Error('مقادیر تخفیف و مالیات باید عدد معتبر با حداکثر دو رقم اعشار باشند.');
            }
            const input = {
                discount,
                tax,
                items: items.map((item) => ({ ...item, ingredientId: item.ingredientId })),
            };
            if (isEdit) return updatePurchaseOrder.execute(id!, input);
            return createPurchaseOrder.execute({
                supplierId,
                orderDate,
                expectedDate: expectedDate || null,
                ...input,
            });
        },
        onSuccess: async (saved) => {
            await queryClient.invalidateQueries({ queryKey: ['purchase-orders', userId, businessId] });
            navigate(`/purchase/orders/${saved.id}`);
        },
        onError: (error) => setFormError(errorMessage(error)),
    });

    const loading = suppliers.isLoading || ingredients.isLoading || (isEdit && order.isLoading);
    if (isEdit && !canUpdate) return <Container maxWidth="md" dir="rtl" sx={{ py: 3 }}><Alert severity="error">مجوز ویرایش سفارش خرید را ندارید.</Alert></Container>;
    if (!isEdit && !canCreate) return <Container maxWidth="md" dir="rtl" sx={{ py: 3 }}><Alert severity="error">مجوز ایجاد سفارش خرید را ندارید.</Alert></Container>;

    const updateLine = (key: string, patch: Partial<DraftLine>) =>
        setLines((current) => current.map((line) => line.key === key ? { ...line, ...patch } : line));
    const submit = (event: FormEvent) => {
        event.preventDefault();
        setFormError('');
        mutation.mutate();
    };

    return (
        <Container maxWidth="lg" dir="rtl" sx={{ py: 2 }}>
            <Stack spacing={2.5}>
                <Box>
                    <Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>{isEdit ? 'ویرایش سفارش خرید' : 'ایجاد سفارش خرید'}</Typography>
                    <Typography color="text.secondary">اطلاعات سفارش و اقلام موردنیاز را ثبت کنید. مبلغ نهایی در سرور محاسبه می‌شود.</Typography>
                </Box>
                {loading && <Box role="status" sx={{ display: 'flex', justifyContent: 'center', py: 4 }}><CircularProgress /></Box>}
                {(order.isError || suppliers.isError || ingredients.isError) && <Alert severity="error" action={<Button color="inherit" onClick={() => { void Promise.all([order.refetch(), suppliers.refetch(), ingredients.refetch()]); }}>تلاش مجدد</Button>}>بارگذاری اطلاعات اولیه ناموفق بود. {errorMessage(order.error ?? suppliers.error ?? ingredients.error)}</Alert>}
                {!isEdit && suppliers.data?.length === 0 && <Alert severity="warning">برای ساخت سفارش ابتدا باید یک تأمین‌کننده فعال ثبت شود.</Alert>}
                {ingredients.data?.length === 0 && <Alert severity="warning">برای ساخت سفارش، ابتدا باید ماده اولیه فعال ثبت شود.</Alert>}
                {formError && <Alert severity="error" onClose={() => setFormError('')}>{formError}</Alert>}
                {isEdit && order.data?.status !== 'draft' && <Alert severity="warning">فقط سفارش پیش‌نویس قابل ویرایش است.</Alert>}
                {!loading && suppliers.data && ingredients.data && (!isEdit || order.data) && <Paper component="form" onSubmit={submit} sx={{ p: { xs: 2, sm: 3 } }}>
                    <Stack spacing={2.5}>
                        <TextField select required label="تأمین‌کننده" value={supplierId} onChange={(event) => setSupplierId(event.target.value)} disabled={isEdit || mutation.isPending}>
                            {(suppliers.data ?? []).map((supplier) => <MenuItem key={supplier.id} value={supplier.id}>{supplier.name}</MenuItem>)}
                        </TextField>
                        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                            <TextField required type="date" label="تاریخ سفارش" value={orderDate} onChange={(event) => setOrderDate(event.target.value)} disabled={isEdit || mutation.isPending} fullWidth slotProps={{ inputLabel: { shrink: true } }} />
                            <TextField type="date" label="تاریخ تحویل مورد انتظار" value={expectedDate} onChange={(event) => setExpectedDate(event.target.value)} disabled={isEdit || mutation.isPending} fullWidth slotProps={{ inputLabel: { shrink: true } }} />
                        </Stack>
                        <Stack direction="row" alignItems="center" justifyContent="space-between">
                            <Typography variant="h6">اقلام سفارش</Typography>
                            <Button type="button" onClick={() => setLines((current) => [...current, newLine()])} disabled={mutation.isPending}>افزودن قلم</Button>
                        </Stack>
                        {lines.map((line, index) => (
                            <Paper key={line.key} variant="outlined" sx={{ p: 2 }}>
                                <Stack spacing={1.5}>
                                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                                        <Typography fontWeight={700}>قلم {index + 1}</Typography>
                                        <Button color="error" size="small" type="button" disabled={lines.length === 1 || mutation.isPending} onClick={() => setLines((current) => current.filter((item) => item.key !== line.key))}>حذف</Button>
                                    </Stack>
                                    <TextField select required label="ماده اولیه" value={line.ingredientId} onChange={(event) => updateLine(line.key, { ingredientId: event.target.value })} disabled={mutation.isPending}>
                                        {(ingredients.data ?? []).map((ingredient) => <MenuItem key={ingredient.id} value={ingredient.id}>{ingredient.name}{ingredient.sku ? ` — ${ingredient.sku}` : ''}</MenuItem>)}
                                    </TextField>
                                    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                                        <TextField required label="مقدار" value={line.quantity} onChange={(event) => updateLine(line.key, { quantity: event.target.value })} inputProps={{ inputMode: 'decimal' }} fullWidth disabled={mutation.isPending} />
                                        <TextField select required label="واحد خرید" value={line.purchaseUnit} onChange={(event) => updateLine(line.key, { purchaseUnit: event.target.value as PurchaseUnit })} fullWidth disabled={mutation.isPending}>
                                            {units.map((unit) => <MenuItem key={unit.value} value={unit.value}>{unit.label}</MenuItem>)}
                                        </TextField>
                                        <TextField required label="قیمت واحد" value={line.unitPrice} onChange={(event) => updateLine(line.key, { unitPrice: event.target.value })} inputProps={{ inputMode: 'decimal' }} fullWidth disabled={mutation.isPending} />
                                    </Stack>
                                </Stack>
                            </Paper>
                        ))}
                        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                            <TextField label="تخفیف مبلغی" value={discount} onChange={(event) => setDiscount(event.target.value)} inputProps={{ inputMode: 'decimal' }} fullWidth disabled={mutation.isPending} />
                            <TextField label="مالیات مبلغی" value={tax} onChange={(event) => setTax(event.target.value)} inputProps={{ inputMode: 'decimal' }} fullWidth disabled={mutation.isPending} />
                        </Stack>
                        <Alert severity="info">مبالغ به واحد پولی مورد استفاده سیستم وارد می‌شوند. تخفیف و مالیات مبلغ ثابت هستند، نه درصد.</Alert>
                        <Stack direction="row" spacing={1}>
                            <Button type="submit" variant="contained" disabled={mutation.isPending || loading || (isEdit && order.data?.status !== 'draft')}>
                                {mutation.isPending ? <CircularProgress size={20} color="inherit" /> : isEdit ? 'ذخیره تغییرات' : 'ایجاد سفارش'}
                            </Button>
                            <Button type="button" onClick={() => navigate(isEdit ? `/purchase/orders/${id}` : '/purchase/orders')} disabled={mutation.isPending}>انصراف</Button>
                        </Stack>
                    </Stack>
                </Paper>}
            </Stack>
        </Container>
    );
};
