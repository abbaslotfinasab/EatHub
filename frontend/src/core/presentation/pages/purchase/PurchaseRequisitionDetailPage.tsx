import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Alert, Box, Button, CircularProgress, Container, Dialog, DialogActions, DialogContent, DialogTitle, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { Link, useParams } from 'react-router-dom';
import {
    approvePurchaseRequisition,
    getPurchaseRequisition,
    getPurchaseRequisitionDecisions,
    getPurchaseRequisitionOrderSummary,
    rejectPurchaseRequisition,
    submitPurchaseRequisition,
} from '../../../data/di/purchaseRequisition.ts';
import type { PurchaseRequisition } from '../../../domain/entities/inventory/PurchaseRequisition.ts';
import { IngredientRepositoryImpl } from '../../../data/repositories/IngredientRepositoryImpl.ts';
import { useAuthStore } from '../../store/auth.store.ts';

const statusLabels: Record<string, string> = {
    draft: 'پیش‌نویس', submitted: 'در انتظار بررسی', approved: 'تأییدشده', rejected: 'ردشده', completed: 'تکمیل‌شده',
};
const formatDate = (value: string) => new Date(value).toLocaleString('fa-IR');
const actionError = (error: unknown) => {
    const response = (error as { response?: { status?: number; data?: unknown } })?.response;
    if (response?.status === 403) return 'مجوز انجام این عملیات را ندارید.';
    if (response?.data) return JSON.stringify(response.data);
    return error instanceof Error ? error.message : 'عملیات ناموفق بود.';
};

export const PurchaseRequisitionDetailPage = () => {
    const { id = '' } = useParams();
    const queryClient = useQueryClient();
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    const permissions = useAuthStore((state) => state.me?.active_business?.permissions ?? []);
    const canView = permissions.includes('purchase.view');
    const canViewOwn = permissions.includes('purchase.requisition.view_own');
    const canSubmit = permissions.includes('purchase.requisition.submit');
    const canApprove = permissions.includes('purchase.requisition.approve');
    const ingredientRepository = useMemo(() => new IngredientRepositoryImpl(), []);
    const [rejectOpen, setRejectOpen] = useState(false);
    const [rejectReason, setRejectReason] = useState('');

    const requisition = useQuery({
        queryKey: ['purchase-requisition', userId, businessId, id],
        queryFn: () => getPurchaseRequisition.execute(id),
        enabled: Boolean(id && userId && businessId && (canView || canViewOwn)),
    });
    const summary = useQuery({
        queryKey: ['purchase-requisition-summary', userId, businessId, id],
        queryFn: () => getPurchaseRequisitionOrderSummary.execute(id),
        enabled: Boolean(id && userId && businessId && (canView || canViewOwn)),
    });
    const decisions = useQuery({
        queryKey: ['purchase-requisition-decisions', userId, businessId, id],
        queryFn: () => getPurchaseRequisitionDecisions.execute(id),
        enabled: Boolean(id && userId && businessId && (canView || canViewOwn)),
    });
    const ingredientIds = useMemo(() => [...new Set([
        ...(requisition.data?.items.map((item) => item.ingredientId) ?? []),
        ...(summary.data?.items.map((item) => item.ingredientId) ?? []),
    ])], [requisition.data, summary.data]);
    const ingredients = useQuery({
        queryKey: ['purchase-requisition-ingredients', userId, businessId, ingredientIds],
        queryFn: () => ingredientRepository.findByIds(ingredientIds),
        enabled: Boolean(userId && businessId && ingredientIds.length),
    });
    const ingredientNames = useMemo(() => new Map((ingredients.data ?? []).map((item) => [item.id, item.name])), [ingredients.data]);

    const actionMutation = useMutation({
        mutationFn: async (action: { type: 'submit' | 'approve' | 'reject'; reason?: string }): Promise<PurchaseRequisition> => {
            if (action.type === 'submit') return submitPurchaseRequisition.execute(id);
            if (action.type === 'approve') return approvePurchaseRequisition.execute(id);
            return rejectPurchaseRequisition.execute(id, action.reason ?? '');
        },
        onSuccess: async () => {
            await Promise.all([
                queryClient.invalidateQueries({ queryKey: ['purchase-requisition', userId, businessId, id] }),
                queryClient.invalidateQueries({ queryKey: ['purchase-requisition-summary', userId, businessId, id] }),
                queryClient.invalidateQueries({ queryKey: ['purchase-requisition-decisions', userId, businessId, id] }),
                queryClient.invalidateQueries({ queryKey: ['purchase-requisitions', userId, businessId] }),
            ]);
            setRejectOpen(false);
            setRejectReason('');
        },
    });

    const hasError = requisition.isError || summary.isError || decisions.isError;
    const errorStatus = (requisition.error as { response?: { status?: number } } | null)?.response?.status
        ?? (summary.error as { response?: { status?: number } } | null)?.response?.status
        ?? (decisions.error as { response?: { status?: number } } | null)?.response?.status;
    const loading = requisition.isLoading || summary.isLoading || decisions.isLoading;
    const current = requisition.data;
    const canSubmitOwnDraft = Boolean(current && current.status === 'draft' && current.requestedById === String(userId) && canSubmit);
    const canDecide = Boolean(current?.status === 'submitted' && canApprove);

    return (
        <Container maxWidth="lg" dir="rtl" sx={{ py: 3 }}>
            <Stack spacing={2.5}>
                <Stack direction={{ xs: 'column', sm: 'row' }} sx={{ justifyContent: 'space-between', alignItems: { sm: 'center' }, gap: 1 }}>
                    <Box>
                        <Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>جزئیات درخواست خرید #{id}</Typography>
                        <Typography color="text.secondary">مقادیر سفارش و مانده از سرویس مرجع درخواست خرید دریافت می‌شوند.</Typography>
                    </Box>
                    <Button component={Link} to="/purchase/requisitions">بازگشت به فهرست</Button>
                </Stack>
                {!canView && !canViewOwn && <Alert severity="error">مجوز مشاهده درخواست خرید را ندارید.</Alert>}
                {loading && <Box role="status" sx={{ display: 'flex', justifyContent: 'center', py: 5 }}><CircularProgress /></Box>}
                {hasError && <Alert severity="error">بارگذاری جزئیات درخواست ناموفق بود. {errorStatus === 403 ? 'دسترسی کافی ندارید.' : errorStatus === 404 ? 'درخواست پیدا نشد.' : 'دوباره تلاش کنید.'}<Button size="small" onClick={() => { void Promise.all([requisition.refetch(), summary.refetch(), decisions.refetch()]); }}>تلاش مجدد</Button></Alert>}
                {actionMutation.isError && <Alert severity="error">{actionError(actionMutation.error)}</Alert>}
                {current && <>
                    <Paper sx={{ p: 2.5 }}>
                        <Stack spacing={1.5}>
                            <Typography variant="h6">اطلاعات درخواست</Typography>
                            <Typography>وضعیت: <strong>{statusLabels[current.status] ?? current.status}</strong></Typography>
                            <Typography>درخواست‌دهنده: {current.requestedById}</Typography>
                            <Typography>تاریخ ثبت: {formatDate(current.createdAt)}</Typography>
                            <Typography>آخرین تغییر: {formatDate(current.updatedAt)}</Typography>
                            <Typography>دلیل درخواست: {current.reason || '—'}</Typography>
                            {(canSubmitOwnDraft || canDecide) && <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
                                {canSubmitOwnDraft && <Button variant="contained" disabled={actionMutation.isPending} onClick={() => actionMutation.mutate({ type: 'submit' })}>ارسال برای بررسی</Button>}
                                {canDecide && <>
                                    <Button variant="contained" color="success" disabled={actionMutation.isPending} onClick={() => actionMutation.mutate({ type: 'approve' })}>تأیید درخواست</Button>
                                    <Button variant="outlined" color="error" disabled={actionMutation.isPending} onClick={() => setRejectOpen(true)}>رد درخواست</Button>
                                </>}
                            </Stack>}
                        </Stack>
                    </Paper>
                    {summary.data && <Box>
                        <Typography variant="h6" sx={{ mb: 1.5 }}>مقدار درخواستی، سفارش‌شده و مانده</Typography>
                        {summary.data.items.length === 0 ? <Alert severity="info">این درخواست قلمی برای نمایش ندارد.</Alert> : <Paper sx={{ overflowX: 'auto' }}>
                            <Table aria-label="خلاصه مقادیر درخواست خرید">
                                <TableHead><TableRow><TableCell>ماده اولیه</TableCell><TableCell>مقدار درخواستی</TableCell><TableCell>مقدار سفارش‌شده</TableCell><TableCell>مانده</TableCell></TableRow></TableHead>
                                <TableBody>{summary.data.items.map((item) => <TableRow key={item.ingredientId}>
                                    <TableCell>{ingredientNames.get(item.ingredientId) ?? `ماده #${item.ingredientId}`}</TableCell>
                                    <TableCell>{item.requestedQuantity}</TableCell>
                                    <TableCell>{item.orderedQuantity}</TableCell>
                                    <TableCell><strong>{item.remainingQuantity}</strong></TableCell>
                                </TableRow>)}</TableBody>
                            </Table>
                        </Paper>}
                    </Box>}
                    <Box>
                        <Typography variant="h6" sx={{ mb: 1.5 }}>تاریخچه تصمیم‌ها</Typography>
                        {decisions.data?.length === 0 ? <Alert severity="info">هنوز تصمیمی برای این درخواست ثبت نشده است.</Alert> : <Paper sx={{ overflowX: 'auto' }}>
                            <Table aria-label="تاریخچه تصمیم‌های درخواست خرید">
                                <TableHead><TableRow><TableCell>تصمیم</TableCell><TableCell>ثبت‌کننده</TableCell><TableCell>وضعیت قبلی</TableCell><TableCell>وضعیت جدید</TableCell><TableCell>زمان</TableCell><TableCell>دلیل رد</TableCell></TableRow></TableHead>
                                <TableBody>{(decisions.data ?? []).map((decision, index) => <TableRow key={`${decision.decidedAt}-${index}`}>
                                    <TableCell>{decision.decision}</TableCell><TableCell>{decision.actorName}</TableCell>
                                    <TableCell>{statusLabels[decision.previousStatus] ?? decision.previousStatus}</TableCell>
                                    <TableCell>{statusLabels[decision.resultingStatus] ?? decision.resultingStatus}</TableCell>
                                    <TableCell>{formatDate(decision.decidedAt)}</TableCell><TableCell>{decision.rejectionReason || '—'}</TableCell>
                                </TableRow>)}</TableBody>
                            </Table>
                        </Paper>}
                    </Box>
                    <Box>
                        <Typography variant="h6" sx={{ mb: 1.5 }}>اقلام درخواست</Typography>
                        <Paper sx={{ overflowX: 'auto' }}>
                            <Table aria-label="اقلام درخواست خرید">
                                <TableHead><TableRow><TableCell>ماده اولیه</TableCell><TableCell>مقدار</TableCell><TableCell>یادداشت</TableCell></TableRow></TableHead>
                                <TableBody>{current.items.map((item, index) => <TableRow key={`${item.ingredientId}-${index}`}>
                                    <TableCell>{ingredientNames.get(item.ingredientId) ?? `ماده #${item.ingredientId}`}</TableCell><TableCell>{item.quantity}</TableCell><TableCell>{item.note || '—'}</TableCell>
                                </TableRow>)}</TableBody>
                            </Table>
                        </Paper>
                    </Box>
                </>}
            </Stack>
            <Dialog open={rejectOpen} onClose={() => !actionMutation.isPending && setRejectOpen(false)} fullWidth maxWidth="sm">
                <DialogTitle>رد درخواست خرید</DialogTitle>
                <DialogContent>
                    <TextField autoFocus fullWidth multiline minRows={3} label="دلیل رد" value={rejectReason} onChange={(event) => setRejectReason(event.target.value)} sx={{ mt: 1 }} disabled={actionMutation.isPending} />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setRejectOpen(false)} disabled={actionMutation.isPending}>انصراف</Button>
                    <Button color="error" variant="contained" onClick={() => actionMutation.mutate({ type: 'reject', reason: rejectReason })} disabled={actionMutation.isPending}>ثبت رد درخواست</Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};
