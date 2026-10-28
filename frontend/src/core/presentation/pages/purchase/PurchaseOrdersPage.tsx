import { useQuery } from '@tanstack/react-query';
import { Alert, Box, Button, CircularProgress, Container, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { listPurchaseSuppliers, listReceivingOrders } from '../../../data/di/purchaseReceiving.ts';
import { useAuthStore } from '../../store/auth.store.ts';

const labels: Record<string, string> = {
    draft: 'پیش‌نویس', sent: 'ارسال‌شده', partial: 'دریافت جزئی', received: 'دریافت کامل', cancelled: 'لغوشده',
};

export const PurchaseOrdersPage = () => {
    const navigate = useNavigate();
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    const permissions = useAuthStore((state) => state.me?.active_business?.permissions ?? []);
    const canView = permissions.includes('purchase.view');
    const canReceive = permissions.includes('purchase.receipt.create');
    const orders = useQuery({
        queryKey: ['purchase-orders', userId, businessId],
        queryFn: () => listReceivingOrders.execute(),
        enabled: Boolean(canView && userId !== null && businessId !== null),
    });
    const suppliers = useQuery({
        queryKey: ['purchase-suppliers', userId, businessId],
        queryFn: () => listPurchaseSuppliers.execute(),
        enabled: Boolean(canView && userId !== null && businessId !== null),
    });
    const supplierById = new Map((suppliers.data ?? []).map((supplier) => [supplier.id, supplier.name]));

    return (
        <Container maxWidth="xl" dir="rtl" sx={{ py: 3 }}>
            <Stack spacing={2.5}>
                <Box>
                    <Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>سفارش‌های خرید</Typography>
                    <Typography color="text.secondary">مشاهده سفارش‌ها و ثبت دریافت واقعی کالا در انبار</Typography>
                </Box>
                {!canView && <Alert severity="error">برای مشاهده سفارش‌های خرید، مجوز مشاهده خرید لازم است.</Alert>}
                {orders.isLoading && <Box role="status" sx={{ display: 'flex', justifyContent: 'center', py: 5 }}><CircularProgress /></Box>}
                {orders.isError && <Alert severity="error" action={<Button color="inherit" size="small" onClick={() => { void Promise.all([orders.refetch(), suppliers.refetch()]); }}>تلاش مجدد</Button>}>دریافت سفارش‌های خرید ناموفق بود. {errorMessage(orders.error)}</Alert>}
                {suppliers.isError && <Alert severity="warning" action={<Button color="inherit" size="small" onClick={() => { void suppliers.refetch(); }}>تلاش مجدد</Button>}>نام تأمین‌کننده‌ها بارگذاری نشد؛ شناسه تأمین‌کننده برای تشخیص سفارش نمایش داده می‌شود.</Alert>}
                {!orders.isLoading && !orders.isError && orders.data?.length === 0 && <Alert severity="info">سفارش خریدی برای این کسب‌وکار ثبت نشده است.</Alert>}
                {!!orders.data?.length && <Paper sx={{ overflowX: 'auto' }}>
                    <Table aria-label="سفارش‌های خرید">
                        <TableHead><TableRow><TableCell>شماره</TableCell><TableCell>تأمین‌کننده</TableCell><TableCell>تاریخ سفارش</TableCell><TableCell>وضعیت</TableCell><TableCell>ردیف‌ها</TableCell><TableCell>عملیات</TableCell></TableRow></TableHead>
                        <TableBody>{orders.data.map((order) => {
                            const eligible = order.status === 'sent' || order.status === 'partial';
                            return <TableRow key={order.id} hover>
                                <TableCell>#{order.id}</TableCell>
                                <TableCell>{supplierById.get(order.supplierId) ?? `شناسه ${order.supplierId}`}</TableCell>
                                <TableCell>{order.orderDate}</TableCell>
                                <TableCell>{labels[order.status] ?? order.status}</TableCell>
                                <TableCell>{order.items.length}</TableCell>
                                <TableCell>
                                    {eligible && canReceive
                                        ? <Button variant="contained" size="small" onClick={() => navigate(`/purchase/orders/${order.id}/receive`)}>ثبت دریافت کالا</Button>
                                        : <Typography variant="body2" color="text.secondary">{!eligible ? 'قابل دریافت نیست' : 'مجوز ثبت دریافت ندارید'}</Typography>}
                                </TableCell>
                            </TableRow>;
                        })}</TableBody>
                    </Table>
                </Paper>}
            </Stack>
        </Container>
    );
};

function errorMessage(error: unknown): string {
    const response = (error as { response?: { status?: number } })?.response;
    if (response?.status === 403) return 'دسترسی کافی ندارید.';
    if (response?.status === 404) return 'منبع موردنظر پیدا نشد.';
    return 'اتصال را بررسی و دوباره تلاش کنید.';
}
