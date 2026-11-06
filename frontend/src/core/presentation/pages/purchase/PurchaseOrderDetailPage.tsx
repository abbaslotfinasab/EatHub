import { useMemo } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Alert, Box, Button, CircularProgress, Container, Divider, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import { getReceivingOrder, listPurchaseSuppliers, sendPurchaseOrder, cancelPurchaseOrder } from '../../../data/di/purchaseReceiving.ts';
import { IngredientRepositoryImpl } from '../../../data/repositories/IngredientRepositoryImpl.ts';
import { useAuthStore } from '../../store/auth.store.ts';

const statusLabels: Record<string, string> = {
    draft: 'پیش‌نویس',
    sent: 'ارسال‌شده',
    partial: 'دریافت جزئی',
    received: 'دریافت کامل',
    cancelled: 'لغوشده',
};
const formatMoney = (value: string) => Number(value).toLocaleString('fa-IR', { maximumFractionDigits: 2 });
const errorMessage = (error: unknown) => {
    const response = (error as { response?: { status?: number; data?: unknown } })?.response;
    if (response?.status === 403) return 'مجوز لازم برای این عملیات را ندارید.';
    if (response?.data) return JSON.stringify(response.data);
    return error instanceof Error ? error.message : 'عملیات ناموفق بود؛ دوباره تلاش کنید.';
};

export const PurchaseOrderDetailPage = () => {
    const { id = '' } = useParams();
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    const permissions = useAuthStore((state) => state.me?.active_business?.permissions ?? []);
    const canView = permissions.includes('purchase.view');
    const canEdit = permissions.includes('purchase.order.update');
    const canSend = permissions.includes('purchase.order.dispatch');
    const canCancel = permissions.includes('purchase.order.cancel');
    const canReceive = permissions.includes('purchase.receipt.create');
    const ingredientRepository = useMemo(() => new IngredientRepositoryImpl(), []);
    const order = useQuery({
        queryKey: ['purchase-orders', userId, businessId, id],
        queryFn: () => getReceivingOrder.execute(id),
        enabled: Boolean(canView && userId && businessId && id),
    });
    const suppliers = useQuery({
        queryKey: ['purchase-suppliers', userId, businessId],
        queryFn: () => listPurchaseSuppliers.execute(),
        enabled: Boolean(canView && userId && businessId),
    });
    const ingredients = useQuery({
        queryKey: ['purchase-order-detail-ingredients', userId, businessId, id, order.data?.items.map((item) => item.ingredientId)],
        queryFn: () => ingredientRepository.findByIds([...new Set((order.data?.items ?? []).map((item) => item.ingredientId))]),
        enabled: Boolean(canView && order.data?.items.length),
    });
    const supplierName = suppliers.data?.find((supplier) => supplier.id === order.data?.supplierId)?.name;
    const ingredientNames = new Map((ingredients.data ?? []).map((ingredient) => [ingredient.id, ingredient.name]));

    const invalidate = async () => {
        await Promise.all([
            queryClient.invalidateQueries({ queryKey: ['purchase-orders', userId, businessId] }),
            queryClient.invalidateQueries({ queryKey: ['purchase-orders', userId, businessId, id] }),
        ]);
    };
    const send = useMutation({ mutationFn: () => sendPurchaseOrder.execute(id), onSuccess: invalidate });
    const cancel = useMutation({ mutationFn: () => cancelPurchaseOrder.execute(id), onSuccess: invalidate });
    const actionError = send.error ?? cancel.error;
    const loading = order.isLoading || suppliers.isLoading;

    if (!canView) return <Container maxWidth="md" dir="rtl" sx={{ py: 3 }}><Alert severity="error">مجوز مشاهده سفارش‌های خرید را ندارید.</Alert></Container>;

    return (
        <Container maxWidth="lg" dir="rtl" sx={{ py: 2 }}>
            <Stack spacing={2.5}>
                <Stack direction={{ xs: 'column', sm: 'row' }} sx={{ justifyContent: 'space-between', alignItems: { sm: 'center' }, gap: 1 }}>
                    <Box>
                        <Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>جزئیات سفارش خرید #{id}</Typography>
                        <Typography color="text.secondary">مشاهده اقلام، مبالغ و وضعیت گردش سفارش</Typography>
                    </Box>
                    <Button onClick={() => navigate('/purchase/orders')}>بازگشت به سفارش‌ها</Button>
                </Stack>
                {loading && <Box role="status" sx={{ display: 'flex', justifyContent: 'center', py: 5 }}><CircularProgress /></Box>}
                {order.isError && <Alert severity="error" action={<Button color="inherit" onClick={() => void order.refetch()}>تلاش مجدد</Button>}>{errorMessage(order.error)}</Alert>}
                {suppliers.isError && <Alert severity="warning">اطلاعات تأمین‌کننده بارگذاری نشد.</Alert>}
                {actionError && <Alert severity="error">{errorMessage(actionError)}</Alert>}
                {order.data && <>
                    <Paper sx={{ p: 2.5 }}>
                        <Stack sx={{ flexDirection: { xs: 'column', sm: 'row' }, flexWrap: 'wrap', gap: 2 }}>
                            <Typography><strong>تأمین‌کننده:</strong> {supplierName ?? `شناسه ${order.data.supplierId}`}</Typography>
                            <Typography><strong>وضعیت:</strong> {statusLabels[order.data.status] ?? order.data.status}</Typography>
                            <Typography><strong>تاریخ سفارش:</strong> {order.data.orderDate}</Typography>
                            <Typography><strong>تحویل مورد انتظار:</strong> {order.data.expectedDate ?? 'تعیین نشده'}</Typography>
                            {order.data.requisitionId && <Typography><strong>درخواست مرتبط:</strong> #{order.data.requisitionId}</Typography>}
                        </Stack>
                        <Divider sx={{ my: 2 }} />
                        <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 1 }}>
                            {order.data.status === 'draft' && canEdit && <Button variant="outlined" onClick={() => navigate(`/purchase/orders/${id}/edit`)}>ویرایش پیش‌نویس</Button>}
                            {order.data.status === 'draft' && canSend && <Button variant="contained" disabled={!order.data.items.length || send.isPending} onClick={() => send.mutate()}>{send.isPending ? 'در حال ارسال...' : 'ارسال سفارش'}</Button>}
                            {['draft', 'sent', 'partial'].includes(order.data.status) && canCancel && <Button color="error" variant="outlined" disabled={cancel.isPending} onClick={() => {
                                if (window.confirm('از لغو این سفارش مطمئن هستید؟')) cancel.mutate();
                            }}>{cancel.isPending ? 'در حال لغو...' : 'لغو سفارش'}</Button>}
                            {['sent', 'partial'].includes(order.data.status) && canReceive && <Button variant="contained" color="success" onClick={() => navigate(`/purchase/orders/${id}/receive`)}>ثبت دریافت کالا</Button>}
                        </Stack>
                    </Paper>
                    <Paper sx={{ overflowX: 'auto' }}>
                        <Box sx={{ p: 2 }}><Typography variant="h6">اقلام سفارش</Typography></Box>
                        <Table size="small" aria-label="اقلام سفارش خرید">
                            <TableHead><TableRow><TableCell>ماده اولیه</TableCell><TableCell>مقدار</TableCell><TableCell>واحد</TableCell><TableCell>قیمت واحد</TableCell><TableCell>جمع ردیف</TableCell></TableRow></TableHead>
                            <TableBody>
                                {order.data.items.map((item) => <TableRow key={item.id}>
                                    <TableCell>{ingredientNames.get(item.ingredientId) ?? `ماده #${item.ingredientId}`}</TableCell>
                                    <TableCell>{item.orderedQuantity}</TableCell>
                                    <TableCell>{item.purchaseUnit ?? '—'}</TableCell>
                                    <TableCell>{formatMoney(item.unitPrice)}</TableCell>
                                    <TableCell>{formatMoney(String(Number(item.orderedQuantity) * Number(item.unitPrice)))}</TableCell>
                                </TableRow>)}
                                {!order.data.items.length && <TableRow><TableCell colSpan={5}>این سفارش قلمی ندارد.</TableCell></TableRow>}
                            </TableBody>
                        </Table>
                        <Divider />
                        <Stack spacing={1} sx={{ p: 2, maxWidth: 360, mr: 'auto' }}>
                            <Stack direction="row" sx={{ justifyContent: 'space-between' }}><Typography color="text.secondary">جمع اقلام</Typography><Typography>{formatMoney(order.data.subtotal)}</Typography></Stack>
                            <Stack direction="row" sx={{ justifyContent: 'space-between' }}><Typography color="text.secondary">تخفیف</Typography><Typography>{formatMoney(order.data.discount)}</Typography></Stack>
                            <Stack direction="row" sx={{ justifyContent: 'space-between' }}><Typography color="text.secondary">مالیات</Typography><Typography>{formatMoney(order.data.tax)}</Typography></Stack>
                            <Divider />
                            <Stack direction="row" sx={{ justifyContent: 'space-between' }}><Typography sx={{ fontWeight: 700 }}>مبلغ نهایی</Typography><Typography sx={{ fontWeight: 700 }}>{formatMoney(order.data.total)}</Typography></Stack>
                        </Stack>
                    </Paper>
                </>}
            </Stack>
        </Container>
    );
};
