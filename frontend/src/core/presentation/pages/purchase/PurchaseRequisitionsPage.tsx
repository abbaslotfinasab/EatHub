import { useQuery } from '@tanstack/react-query';
import { Alert, Box, Button, CircularProgress, Container, MenuItem, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listPurchaseRequisitions } from '../../../data/di/purchaseRequisition.ts';
import type { RequisitionStatus } from '../../../domain/entities/inventory/PurchaseRequisition.ts';
import { useAuthStore } from '../../store/auth.store.ts';

const labels: Record<RequisitionStatus, string> = {
    draft: 'پیش‌نویس',
    submitted: 'در انتظار بررسی',
    approved: 'تأییدشده',
    rejected: 'ردشده',
    completed: 'تکمیل‌شده',
};

const errorMessage = (error: unknown) => {
    const status = (error as { response?: { status?: number } })?.response?.status;
    if (status === 403) return 'مجوز مشاهده درخواست‌های خرید را ندارید.';
    if (status === 404) return 'درخواست موردنظر پیدا نشد.';
    return 'دریافت درخواست‌های خرید ناموفق بود. اتصال را بررسی و دوباره تلاش کنید.';
};

export const PurchaseRequisitionsPage = () => {
    const navigate = useNavigate();
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    const permissions = useAuthStore((state) => state.me?.active_business?.permissions ?? []);
    const canView = permissions.includes('purchase.view');
    const canViewOwn = permissions.includes('purchase.requisition.view_own');
    const canCreate = permissions.includes('purchase.requisition.create');
    const [status, setStatus] = useState<'all' | RequisitionStatus>('all');

    const requisitions = useQuery({
        queryKey: ['purchase-requisitions', userId, businessId, status],
        queryFn: () => listPurchaseRequisitions.execute(status === 'all' ? undefined : status),
        enabled: Boolean(userId && businessId && (canView || canViewOwn)),
    });

    return (
        <Container maxWidth="xl" dir="rtl" sx={{ py: 3 }}>
            <Stack spacing={2.5}>
                <Stack direction={{ xs: 'column', sm: 'row' }} sx={{ justifyContent: 'space-between', alignItems: { sm: 'center' }, gap: 1 }}>
                    <Box>
                        <Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>درخواست‌های خرید</Typography>
                        <Typography color="text.secondary">مشاهده وضعیت درخواست‌ها و مقدار سفارش‌شده و مانده هر ماده اولیه</Typography>
                    </Box>
                    {canCreate && <Button variant="contained" onClick={() => navigate('/purchase/requisitions/create')}>ایجاد درخواست خرید</Button>}
                </Stack>
                {!canView && !canViewOwn && <Alert severity="error">برای مشاهده درخواست‌های خرید مجوز لازم را ندارید.</Alert>}
                {requisitions.isLoading && <Box role="status" sx={{ display: 'flex', justifyContent: 'center', py: 5 }}><CircularProgress /></Box>}
                {requisitions.isError && <Alert severity="error" action={<Button color="inherit" size="small" onClick={() => { void requisitions.refetch(); }}>تلاش مجدد</Button>}>{errorMessage(requisitions.error)}</Alert>}
                {!requisitions.isLoading && !requisitions.isError && <>
                    <Stack direction={{ xs: 'column', sm: 'row' }} sx={{ justifyContent: 'space-between', gap: 1 }}>
                        <TextField select label="وضعیت درخواست" value={status} onChange={(event) => setStatus(event.target.value as 'all' | RequisitionStatus)} sx={{ minWidth: 220 }}>
                            <MenuItem value="all">همه وضعیت‌ها</MenuItem>
                            {Object.entries(labels).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
                        </TextField>
                    </Stack>
                    {requisitions.data?.length === 0 && <Alert severity="info">درخواستی برای نمایش وجود ندارد.</Alert>}
                    {!!requisitions.data?.length && <Paper sx={{ overflowX: 'auto' }}>
                        <Table aria-label="درخواست‌های خرید">
                            <TableHead><TableRow><TableCell>شماره درخواست</TableCell><TableCell>وضعیت</TableCell><TableCell>تعداد اقلام</TableCell><TableCell>تاریخ ثبت</TableCell><TableCell>آخرین تغییر</TableCell><TableCell>عملیات</TableCell></TableRow></TableHead>
                            <TableBody>{requisitions.data.map((item) => <TableRow key={item.id} hover>
                                <TableCell>#{item.id}</TableCell>
                                <TableCell>{labels[item.status] ?? item.status}</TableCell>
                                <TableCell>{item.items.length}</TableCell>
                                <TableCell>{new Date(item.createdAt).toLocaleDateString('fa-IR')}</TableCell>
                                <TableCell>{new Date(item.updatedAt).toLocaleDateString('fa-IR')}</TableCell>
                                <TableCell><Button size="small" onClick={() => navigate(`/purchase/requisitions/${item.id}`)}>جزئیات</Button></TableCell>
                            </TableRow>)}</TableBody>
                        </Table>
                    </Paper>}
                </>}
            </Stack>
        </Container>
    );
};
