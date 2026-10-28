import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Box, Button, CircularProgress, Container, MenuItem, Pagination, Paper, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { useGetAllIngredients } from '../hooks/useGetAllIngredients';
import { Unit, type UnitType } from '../../domain/entities/inventory/Ingredient.ts';

export const IngredientsListPage = () => {
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState('');
    const [activeFilter, setActiveFilter] = useState('all');
    const [unit, setUnit] = useState('');
    const { data, isLoading, isError, error } = useGetAllIngredients({
        page,
        pageSize: 20,
        ...(search ? { search } : {}),
        ...(activeFilter !== 'all' ? { isActive: activeFilter === 'active' } : {}),
        ...(unit ? { unit: unit as UnitType } : {}),
        preparationLevel: 'raw',
    });
    const errorStatus = (error as { response?: { status?: number } } | null)?.response?.status;
    const unitLabel = (value: string) => ({ kg: 'کیلوگرم', g: 'گرم', l: 'لیتر', ml: 'میلی‌لیتر', pc: 'عدد', pk: 'بسته' }[value as UnitType] ?? value);

    return (
        <Container maxWidth="xl" sx={{ py: 2 }} dir="rtl">
            <Stack spacing={2.5}>
                <Box>
                    <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>مواد اولیه</Typography>
                    <Typography color="text.secondary">کاتالوگ مواد انبارشده؛ موجودی و بهای کالا در موجودی انبار نگهداری می‌شود.</Typography>
                </Box>
                <Paper component="form" onSubmit={(event) => { event.preventDefault(); setPage(1); }} sx={{ p: 2 }}>
                    <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                        <TextField label="جستجوی نام یا کد" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} size="small" />
                        <TextField select label="وضعیت" value={activeFilter} onChange={(event) => { setActiveFilter(event.target.value); setPage(1); }} size="small" sx={{ minWidth: 150 }}>
                            <MenuItem value="all">همه</MenuItem><MenuItem value="active">فعال</MenuItem><MenuItem value="inactive">غیرفعال</MenuItem>
                        </TextField>
                        <TextField select label="واحد" value={unit} onChange={(event) => { setUnit(event.target.value); setPage(1); }} size="small" sx={{ minWidth: 150 }}>
                            <MenuItem value="">همه</MenuItem>{Object.values(Unit).map((value) => <MenuItem key={value} value={value}>{unitLabel(value)}</MenuItem>)}
                        </TextField>
                        <Button component={Link} to="/ingredients/create" variant="contained">ماده جدید</Button>
                    </Stack>
                </Paper>
                {isLoading && <Box role="status" sx={{ display: 'flex', justifyContent: 'center', py: 5 }}><CircularProgress /></Box>}
                {isError && <Alert severity="error">{errorStatus === 403 ? 'اجازه مشاهده مواد اولیه را ندارید.' : 'دریافت فهرست مواد اولیه ناموفق بود. دوباره تلاش کنید.'}</Alert>}
                {!isLoading && !isError && data?.results.length === 0 && <Alert severity="info">ماده‌ای برای این فیلتر پیدا نشد.</Alert>}
                {!isLoading && !isError && data && data.results.length > 0 && <>
                    <TableContainer component={Paper} sx={{ overflowX: 'auto' }}><Table dir="rtl" aria-label="فهرست مواد اولیه">
                        <TableHead><TableRow><TableCell>نام</TableCell><TableCell>SKU</TableCell><TableCell>واحد</TableCell><TableCell>نوع ماده</TableCell><TableCell>وضعیت</TableCell><TableCell>عملیات</TableCell></TableRow></TableHead>
                        <TableBody>{data.results.map((item) => <TableRow key={item.id} hover>
                            <TableCell>{item.name}</TableCell><TableCell dir="ltr">{item.sku || '—'}</TableCell><TableCell>{unitLabel(item.unit)}</TableCell>
                            <TableCell>ماده اولیه</TableCell><TableCell>{item.isActive ? 'فعال' : 'غیرفعال'}</TableCell>
                            <TableCell><Button component={Link} to={`/ingredients/${item.id}/edit`} size="small">ویرایش</Button></TableCell>
                        </TableRow>)}</TableBody>
                    </Table></TableContainer>
                    <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography color="text.secondary">تعداد کل: {data.count}</Typography>
                        <Pagination page={page} count={Math.max(1, Math.ceil(data.count / 20))} onChange={(_event, value) => setPage(value)} disabled={data.count === 0} />
                    </Stack>
                </>}
            </Stack>
        </Container>
    );
};
