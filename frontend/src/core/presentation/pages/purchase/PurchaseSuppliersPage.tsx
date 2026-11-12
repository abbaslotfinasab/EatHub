import { useMemo, useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
    Alert, Box, Button, CircularProgress, Container, Dialog, DialogActions, DialogContent,
    DialogTitle, MenuItem, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow,
    TextField, Typography,
} from '@mui/material';
import { listPurchaseSuppliersManagement, createPurchaseSupplier, updatePurchaseSupplier } from '../../../data/di/purchaseSupplier.ts';
import type { PurchaseSupplier, PurchaseSupplierInput } from '../../../domain/entities/inventory/PurchaseSupplier.ts';
import { useAuthStore } from '../../store/auth.store.ts';

const emptyForm: PurchaseSupplierInput = {
    name: '', phone: '', email: '', address: '', taxNumber: '', notes: '', isActive: true,
};
const errorMessage = (error: unknown) => {
    const response = (error as { response?: { status?: number; data?: unknown } })?.response;
    if (response?.status === 403) return 'مجوز لازم برای این عملیات را ندارید.';
    if (response?.data) return JSON.stringify(response.data);
    return error instanceof Error ? error.message : 'عملیات ناموفق بود؛ دوباره تلاش کنید.';
};

export const PurchaseSuppliersPage = () => {
    const queryClient = useQueryClient();
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    const permissions = useAuthStore((state) => state.me?.active_business?.permissions ?? []);
    const canView = permissions.includes('purchase.view');
    const canManage = permissions.includes('purchase.supplier.manage');
    const [search, setSearch] = useState('');
    const [status, setStatus] = useState('active');
    const [dialogOpen, setDialogOpen] = useState(false);
    const [editing, setEditing] = useState<PurchaseSupplier | null>(null);
    const [form, setForm] = useState<PurchaseSupplierInput>(emptyForm);
    const [formError, setFormError] = useState('');
    const [pageError, setPageError] = useState('');

    const filters = useMemo(() => ({
        search: search.trim() || undefined,
        isActive: status === 'all' ? undefined : status === 'active',
    }), [search, status]);
    const suppliers = useQuery({
        queryKey: ['purchase-supplier-management', userId, businessId, filters],
        queryFn: () => listPurchaseSuppliersManagement.execute(filters),
        enabled: Boolean(canView && userId && businessId),
    });

    const closeDialog = () => {
        setDialogOpen(false);
        setEditing(null);
        setForm(emptyForm);
        setFormError('');
    };
    const openCreate = () => {
        setEditing(null);
        setForm(emptyForm);
        setFormError('');
        setDialogOpen(true);
    };
    const openEdit = (supplier: PurchaseSupplier) => {
        setEditing(supplier);
        setForm({
            name: supplier.name, phone: supplier.phone, email: supplier.email,
            address: supplier.address, taxNumber: supplier.taxNumber, notes: supplier.notes,
            isActive: supplier.isActive,
        });
        setFormError('');
        setDialogOpen(true);
    };

    const refresh = async () => {
        await Promise.all([
            queryClient.invalidateQueries({ queryKey: ['purchase-supplier-management', userId, businessId] }),
            queryClient.invalidateQueries({ queryKey: ['purchase-suppliers', userId, businessId] }),
        ]);
    };
    const createMutation = useMutation({
        mutationFn: (input: PurchaseSupplierInput) => createPurchaseSupplier.execute(input),
        onSuccess: async () => { await refresh(); closeDialog(); },
        onError: (error) => setFormError(errorMessage(error)),
    });
    const updateMutation = useMutation({
        mutationFn: ({ id, input }: { id: string; input: PurchaseSupplierInput }) => updatePurchaseSupplier.execute(id, input),
        onSuccess: async () => { await refresh(); closeDialog(); },
        onError: (error) => setFormError(errorMessage(error)),
    });

    const submit = (event: FormEvent) => {
        event.preventDefault();
        setFormError('');
        if (editing) updateMutation.mutate({ id: editing.id, input: form });
        else createMutation.mutate(form);
    };
    const saving = createMutation.isPending || updateMutation.isPending;

    return (
        <Container maxWidth="xl" dir="rtl" sx={{ py: 3 }}>
            <Stack spacing={2.5}>
                <Stack direction={{ xs: 'column', sm: 'row' }} sx={{ justifyContent: 'space-between', alignItems: { sm: 'center' }, gap: 1 }}>
                    <Box>
                        <Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>مدیریت تأمین‌کنندگان</Typography>
                        <Typography color="text.secondary">اطلاعات تماس و وضعیت تأمین‌کنندگان کسب‌وکار</Typography>
                    </Box>
                    {canManage && <Button variant="contained" onClick={openCreate}>افزودن تأمین‌کننده</Button>}
                </Stack>
                {!canView && <Alert severity="error">برای مشاهده فهرست تأمین‌کنندگان، مجوز مشاهده خرید لازم است.</Alert>}
                {pageError && <Alert severity="error" onClose={() => setPageError('')}>{pageError}</Alert>}
                {suppliers.isError && <Alert severity="error" action={<Button color="inherit" onClick={() => { void suppliers.refetch(); }}>تلاش مجدد</Button>}>
                    دریافت فهرست تأمین‌کنندگان ناموفق بود. {errorMessage(suppliers.error)}
                </Alert>}
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                    <TextField fullWidth label="جستجو بر اساس نام، تلفن یا اطلاعات تماس" value={search} onChange={(event) => setSearch(event.target.value)} />
                    <TextField select label="وضعیت" value={status} onChange={(event) => setStatus(event.target.value)} sx={{ minWidth: { sm: 200 } }}>
                        <MenuItem value="active">فعال</MenuItem>
                        <MenuItem value="inactive">غیرفعال</MenuItem>
                        <MenuItem value="all">همه</MenuItem>
                    </TextField>
                </Stack>
                {suppliers.isLoading && <Box role="status" sx={{ display: 'flex', justifyContent: 'center', py: 5 }}><CircularProgress /></Box>}
                {!suppliers.isLoading && !suppliers.isError && suppliers.data?.length === 0 && <Alert severity="info">تأمین‌کننده‌ای با این فیلتر پیدا نشد.</Alert>}
                {!!suppliers.data?.length && <Paper sx={{ overflowX: 'auto' }}>
                    <Table aria-label="فهرست تأمین‌کنندگان">
                        <TableHead><TableRow>
                            <TableCell>نام</TableCell><TableCell>تلفن</TableCell><TableCell>ایمیل</TableCell>
                            <TableCell>شماره مالیاتی</TableCell><TableCell>وضعیت</TableCell>
                            {canManage && <TableCell>عملیات</TableCell>}
                        </TableRow></TableHead>
                        <TableBody>{suppliers.data.map((supplier) => <TableRow key={supplier.id} hover>
                            <TableCell>{supplier.name}</TableCell>
                            <TableCell>{supplier.phone || '—'}</TableCell>
                            <TableCell>{supplier.email || '—'}</TableCell>
                            <TableCell>{supplier.taxNumber || '—'}</TableCell>
                            <TableCell>{supplier.isActive ? 'فعال' : 'غیرفعال'}</TableCell>
                            {canManage && <TableCell>
                                <Button size="small" onClick={() => openEdit(supplier)}>ویرایش</Button>
                            </TableCell>}
                        </TableRow>)}</TableBody>
                    </Table>
                </Paper>}
            </Stack>

            <Dialog open={dialogOpen} onClose={saving ? undefined : closeDialog} fullWidth maxWidth="sm">
                <DialogTitle>{editing ? 'ویرایش تأمین‌کننده' : 'افزودن تأمین‌کننده'}</DialogTitle>
                <Box component="form" onSubmit={submit}>
                    <DialogContent>
                        <Stack spacing={2} sx={{ pt: 1 }}>
                            {formError && <Alert severity="error">{formError}</Alert>}
                            <TextField required label="نام تأمین‌کننده" value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} disabled={saving} />
                            <TextField label="شماره تماس" value={form.phone} onChange={(event) => setForm((current) => ({ ...current, phone: event.target.value }))} disabled={saving} />
                            <TextField label="ایمیل" type="email" value={form.email} onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))} disabled={saving} />
                            <TextField label="آدرس" multiline minRows={2} value={form.address} onChange={(event) => setForm((current) => ({ ...current, address: event.target.value }))} disabled={saving} />
                            <TextField label="شماره مالیاتی" value={form.taxNumber} onChange={(event) => setForm((current) => ({ ...current, taxNumber: event.target.value }))} disabled={saving} />
                            <TextField label="توضیحات" multiline minRows={2} value={form.notes} onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))} disabled={saving} />
                            {editing && <TextField select label="وضعیت" value={form.isActive ? 'active' : 'inactive'} onChange={(event) => setForm((current) => ({ ...current, isActive: event.target.value === 'active' }))} disabled={saving}>
                                <MenuItem value="active">فعال</MenuItem><MenuItem value="inactive">غیرفعال</MenuItem>
                            </TextField>}
                        </Stack>
                    </DialogContent>
                    <DialogActions sx={{ px: 3, pb: 2 }}>
                        <Button onClick={closeDialog} disabled={saving}>انصراف</Button>
                        <Button type="submit" variant="contained" disabled={saving || !form.name.trim()}>
                            {saving ? <CircularProgress size={20} color="inherit" /> : editing ? 'ذخیره تغییرات' : 'ثبت تأمین‌کننده'}
                        </Button>
                    </DialogActions>
                </Box>
            </Dialog>
        </Container>
    );
};
