import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Alert, Box, Button, CircularProgress, Container, MenuItem, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { listPurchaseSuppliers, listReceivingOrders } from '../../../data/di/purchaseReceiving.ts';
import { useAuthStore } from '../../store/auth.store.ts';

const labels: Record<string, string> = {
    draft: 'پیش‌نویس', sent: 'ارسال‌شده', partial: 'دریافت جزئی', received: 'دریافت کامل', cancelled: 'لغوشده',
};
const errorMessage = (error: unknown): string => {
    const response = (error as { response?: { status?: number } })?.response;
    if (response?.status === 403) return 'دسترسی کافی ندارید.';
    if (response?.status === 404) return 'منبع موردنظر پیدا نشد.';
    return 'اتصال را بررسی و دوباره تلاش کنید.';
};

export const PurchaseOrdersPage = () => {
    const navigate = useNavigate();
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    const permissions = useAuthStore((state) => state.me?.active_business?.permissions ?? []);
    const canView = permissions.includes('purchase.view');
    const canCreate = permissions.includes('purchase.order.create');
    const canReceive = permissions.includes('purchase.receipt.create');
    const [status, setStatus] = useState('all');
    const [search, setSearch] = useState('');
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
    const supplierById = useMemo(() => new Map((suppliers.data ?? []).map((supplier) => [supplier.id, supplier.name])), [suppliers.data]);
    const filteredOrders = useMemo(() => (orders.data ?? []).filter((order) => {
        const statusMatches = status === 'all' || order.status === status;
        const supplierName = supplierById.get(order.supplierId) ?? '';
        const searchMatches = !search.trim()
            || order.id.includes(search.trim())
            || order.supplierId.includes(search.trim())
            || supplierName.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase());
        return statusMatches && searchMatches;
    }), [orders.data, status, search, supplierById]);

    return (
        <Container maxWidth="xl" dir="rtl" sx={{ py: 3 }}>
            <Stack spacing={2.5}>
                <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems={{ sm: 'center' }} gap={1}>
                    <Box>
                        <Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>سفارش‌های خرید</Typography>
                        <Typography color="text.secondary">مدیریت سفارش‌ها، پیگیری وضعیت و ثبت دریافت کالا در انبار</Typography>
                    </Box>
                    {canCreate && <Button variant="contained" onClick={() => navigate('/purchase/orders/create')}>ایجاد سفارش خرید</Button>}
                </Stack>
                {!canView && <Alert severity="error">برای مشاهده سفارش‌های خرید، مجوز مشاهده خرید لازم است.</Alert>}
                {orders.isLoading && <Box role="status" sx={{ display: 'flex', justifyContent: 'center', py: 5 }}><CircularProgress /></Box>}
                {orders.isError && <Alert severity="error" action={<Button color="inherit" size="small" onClick={() => { void Promise.all([orders.refetch(), suppliers.refetch()]); }}>تلاش مجدد</Button>}>دریافت سفارش‌های خرید ناموفق بود. {errorMessage(orders.error)}</Alert>}
                {suppliers.isError && <Alert severity="warning" action={<Button color="inherit" size="small" onClick={() => { void suppliers.refetch(); }}>تلاش مجدد</Button>}>نام تأمین‌کننده‌ها بارگذاری نشد؛ شناسه تأمین‌کننده نمایش داده می‌شود.</Alert>}
                {!!orders.data?.length && <>
                    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                        <TextField fullWidth label="جستجو بر اساس شماره یا تأمین‌کننده" value={search} onChange={(event) => setSearch(event.target.value)} />
                        <TextField select label="وضعیت" value={status} onChange={(event) => setStatus(event.target.value)} sx={{ minWidth: { sm: 220 } }}>
                            <MenuItem value="all">همه وضعیت‌ها</MenuItem>
                            {Object.entries(labels).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
                        </TextField>
                    </Stack>
                    <Paper sx={{ overflowX: 'auto' }}>
                        <Table aria-label="سفارش‌های خرید">
                            <TableHead><TableRow><TableCell>شماره</TableCell><TableCell>تأمین‌کننده</TableCell><TableCell>تاریخ سفارش</TableCell><TableCell>تحویل مورد انتظار</TableCell><TableCell>وضعیت</TableCell><TableCell>ردیف‌ها</TableCell><TableCell>مبلغ نهایی</TableCell><TableCell>عملیات</TableCell></TableRow></TableHead>
                            <TableBody>{filteredOrders.map((order) => {
                                const eligible = order.status === 'sent' || order.status === 'partial';
                                return <TableRow key={order.id} hover>
                                    <TableCell>#{order.id}</TableCell>
                                    <TableCell>{supplierById.get(order.supplierId) ?? `شناسه ${order.supplierId}`}</TableCell>
                                    <TableCell>{order.orderDate}</TableCell>
                                    <TableCell>{order.expectedDate ?? '—'}</TableCell>
                                    <TableCell>{labels[order.status] ?? order.status}</TableCell>
                                    <TableCell>{order.items.length}</TableCell>
                                    <TableCell>{Number(order.total).toLocaleString('fa-IR')}</TableCell>
                                    <TableCell>
                                        <Stack direction="row" spacing={0.5}>
                                            <Button size="small" onClick={() => navigate(`/purchase/orders/${order.id}`)}>جزئیات</Button>
                                            {eligible && canReceive && <Button size="small" variant="contained" onClick={() => navigate(`/purchase/orders/${order.id}/receive`)}>دریافت</Button>}
                                        </Stack>
                                    </TableCell>
                                </TableRow>;
                            })}</TableBody>
                        </Table>
                    </Paper>
                    {filteredOrders.length === 0 && <Alert severity="info">با فیلترهای انتخاب‌شده سفارشی پیدا نشد.</Alert>}
                </>}
                {!orders.isLoading && !orders.isError && orders.data?.length === 0 && <Alert severity="info">سفارش خریدی برای این کسب‌وکار ثبت نشده است.</Alert>}
            </Stack>
        </Container>
    );
};
