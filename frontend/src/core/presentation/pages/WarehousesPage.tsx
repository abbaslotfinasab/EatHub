import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Alert, Box, Button, Checkbox, CircularProgress, Container, FormControlLabel, MenuItem, Pagination, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { WarehouseRepositoryImpl } from '../../data/repositories/WarehouseRepositoryImpl.ts';
import type { Warehouse, WarehouseInput } from '../../domain/entities/inventory/Warehouse.ts';

const repository = new WarehouseRepositoryImpl();
const errorText = (error: unknown) => {
    const response = (error as { response?: { status?: number; data?: unknown } })?.response;
    if (response?.status === 403) return 'اجازه مدیریت انبارها را ندارید.';
    if (response?.status === 400) return 'اطلاعات واردشده معتبر نیست. نام و کد انبار را بررسی کنید.';
    return 'ارتباط با سرور برقرار نشد. دوباره تلاش کنید.';
};

export const WarehousesPage = () => {
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState('');
    const [activeFilter, setActiveFilter] = useState('all');
    const [defaultFilter, setDefaultFilter] = useState('all');
    const [editing, setEditing] = useState<Warehouse | null>(null);
    const [name, setName] = useState('');
    const [code, setCode] = useState('');
    const [active, setActive] = useState(true);
    const [isDefault, setIsDefault] = useState(false);
    const [feedback, setFeedback] = useState('');
    const query = useQuery({
        queryKey: ['warehouses', page, search, activeFilter, defaultFilter],
        queryFn: () => repository.list({
            page, pageSize: 20,
            ...(search ? { search } : {}),
            ...(activeFilter !== 'all' ? { isActive: activeFilter === 'active' } : {}),
            ...(defaultFilter !== 'all' ? { isDefault: defaultFilter === 'default' } : {}),
        }),
    });
    const refresh = async () => { await queryClient.invalidateQueries({ queryKey: ['warehouses'] }); };
    const create = useMutation({ mutationFn: (input: WarehouseInput) => repository.create(input), onSuccess: async () => { setFeedback('انبار با موفقیت ایجاد شد.'); await refresh(); } });
    const update = useMutation({ mutationFn: ({ id, input }: { id: string; input: Partial<WarehouseInput> }) => repository.update(id, input), onSuccess: async () => { setFeedback('تغییرات انبار ذخیره شد.'); await refresh(); } });
    const error = query.error ?? create.error ?? update.error;

    const reset = () => { setEditing(null); setName(''); setCode(''); setActive(true); setIsDefault(false); };
    const edit = (warehouse: Warehouse) => {
        setEditing(warehouse); setName(warehouse.name); setCode(warehouse.code ?? '');
        setActive(warehouse.isActive); setIsDefault(warehouse.isDefault);
    };
    const submit = (event: FormEvent) => {
        event.preventDefault();
        const input = { name: name.trim(), code: code.trim() || null, isActive: active, isDefault };
        if (editing) update.mutate({ id: editing.id, input }, { onSuccess: reset });
        else create.mutate(input, { onSuccess: reset });
    };

    return (
        <Container maxWidth="xl" sx={{ py: 2 }} dir="rtl">
            <Stack spacing={2.5}>
                <Box>
                    <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>انبارها</Typography>
                    <Typography color="text.secondary">مدیریت انبارهای کسب‌وکار و انبار پیش‌فرض دریافت کالا</Typography>
                </Box>
                {error && <Alert severity="error">{errorText(error)}</Alert>}
                {!!feedback && <Alert severity="success" onClose={() => setFeedback('')}>{feedback}</Alert>}
                <Paper component="form" onSubmit={submit} sx={{ p: 2.5 }}>
                    <Stack spacing={2}>
                        <Typography variant="h6">{editing ? 'ویرایش انبار' : 'ایجاد انبار'}</Typography>
                        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                            <TextField required label="نام انبار" value={name} slotProps={{ htmlInput: { maxLength: 120 } }} onChange={(event) => setName(event.target.value)} />
                            <TextField label="کد (اختیاری)" value={code} slotProps={{ htmlInput: { maxLength: 50 } }} onChange={(event) => setCode(event.target.value)} />
                            <FormControlLabel control={<Checkbox checked={active} onChange={(event) => { setActive(event.target.checked); if (!event.target.checked) setIsDefault(false); }} />} label="فعال" />
                            <FormControlLabel control={<Checkbox checked={isDefault} onChange={(event) => setIsDefault(event.target.checked)} disabled={!active} />} label="انبار پیش‌فرض" />
                        </Stack>
                        <Stack direction="row" spacing={1}>
                            <Button type="submit" variant="contained" disabled={create.isPending || update.isPending || !name.trim()}>{editing ? 'ذخیره' : 'ایجاد'}</Button>
                            {editing && <Button type="button" onClick={reset}>لغو ویرایش</Button>}
                        </Stack>
                    </Stack>
                </Paper>
                <Paper sx={{ p: 2 }}>
                    <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                        <TextField label="جستجوی نام یا کد" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} size="small" fullWidth />
                        <TextField select label="وضعیت" value={activeFilter} onChange={(event) => { setActiveFilter(event.target.value); setPage(1); }} size="small" sx={{ minWidth: 140 }}>
                            <MenuItem value="all">همه</MenuItem><MenuItem value="active">فعال</MenuItem><MenuItem value="inactive">غیرفعال</MenuItem>
                        </TextField>
                        <TextField select label="پیش‌فرض" value={defaultFilter} onChange={(event) => { setDefaultFilter(event.target.value); setPage(1); }} size="small" sx={{ minWidth: 140 }}>
                            <MenuItem value="all">همه</MenuItem><MenuItem value="default">پیش‌فرض</MenuItem><MenuItem value="not_default">غیرپیش‌فرض</MenuItem>
                        </TextField>
                    </Stack>
                </Paper>
                {query.isLoading && <Box role="status" sx={{ display: 'flex', justifyContent: 'center', py: 5 }}><CircularProgress /></Box>}
                {!query.isLoading && !query.isError && query.data?.results.length === 0 && <Alert severity="info">انبارهیی ثبت نشده است.</Alert>}
                {!query.isLoading && query.isError && !error && <Alert severity="error">دریافت فهرست انبارها ناموفق بود.</Alert>}
                {!query.isLoading && !query.isError && query.data && query.data.results.length > 0 && <>
                    <Paper sx={{ overflowX: 'auto' }}><Table aria-label="فهرست انبارها" dir="rtl">
                        <TableHead><TableRow><TableCell>نام</TableCell><TableCell>کد</TableCell><TableCell>وضعیت</TableCell><TableCell>پیش‌فرض</TableCell><TableCell>عملیات</TableCell></TableRow></TableHead>
                        <TableBody>{query.data.results.map((warehouse) => <TableRow key={warehouse.id} hover>
                            <TableCell>{warehouse.name}</TableCell><TableCell>{warehouse.code || '—'}</TableCell><TableCell>{warehouse.isActive ? 'فعال' : 'غیرفعال'}</TableCell>
                            <TableCell>{warehouse.isDefault && warehouse.isActive ? <strong>انبار پیش‌فرض</strong> : '—'}</TableCell>
                            <TableCell><Stack direction={{ xs: 'column', md: 'row' }} sx={{ flexWrap: 'wrap' }}><Button size="small" onClick={() => navigate(`/inventory?warehouse_id=${encodeURIComponent(warehouse.id)}`)}>مشاهده موجودی</Button><Button size="small" onClick={() => edit(warehouse)}>ویرایش</Button>
                                {warehouse.isActive
                                    ? <Button size="small" color="warning" onClick={() => update.mutate({ id: warehouse.id, input: { isActive: false } })}>غیرفعال‌سازی</Button>
                                    : <Button size="small" onClick={() => update.mutate({ id: warehouse.id, input: { isActive: true } })}>فعال‌سازی</Button>}
                                {!warehouse.isDefault && warehouse.isActive && <Button size="small" onClick={() => update.mutate({ id: warehouse.id, input: { isDefault: true } })}>تنظیم پیش‌فرض</Button>}
                            </Stack></TableCell>
                        </TableRow>)}</TableBody>
                    </Table></Paper>
                    <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography color="text.secondary">تعداد کل: {query.data.count}</Typography>
                        <Pagination page={page} count={Math.max(1, Math.ceil(query.data.count / 20))} onChange={(_event, value) => setPage(value)} disabled={query.data.count === 0} />
                    </Stack>
                </>}
            </Stack>
        </Container>
    );
};
