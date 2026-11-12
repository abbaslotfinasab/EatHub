import { useMemo, useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Alert, Box, Button, CircularProgress, Container, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { createPurchaseRequisition } from '../../../data/di/purchaseRequisition.ts';
import { IngredientRepositoryImpl } from '../../../data/repositories/IngredientRepositoryImpl.ts';
import { useAuthStore } from '../../store/auth.store.ts';

type DraftLine = { key: string; ingredientId: string; quantity: string; note: string };
const newLine = (): DraftLine => ({
    key: globalThis.crypto?.randomUUID?.() ?? String(Date.now() + Math.random()),
    ingredientId: '',
    quantity: '1',
    note: '',
});
const errorMessage = (error: unknown) => {
    const response = (error as { response?: { status?: number; data?: unknown } })?.response;
    if (response?.status === 403) return 'مجوز ایجاد درخواست خرید را ندارید.';
    if (response?.data) return JSON.stringify(response.data);
    return error instanceof Error ? error.message : 'ثبت درخواست خرید ناموفق بود.';
};

export const CreatePurchaseRequisitionPage = () => {
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    const permissions = useAuthStore((state) => state.me?.active_business?.permissions ?? []);
    const canCreate = permissions.includes('purchase.requisition.create');
    const ingredientRepository = useMemo(() => new IngredientRepositoryImpl(), []);
    const [reason, setReason] = useState('');
    const [lines, setLines] = useState<DraftLine[]>([newLine()]);
    const [formError, setFormError] = useState('');

    const ingredients = useQuery({
        queryKey: ['purchase-requisition-create-ingredients', userId, businessId],
        queryFn: async () => {
            const first = await ingredientRepository.findAll({ page: 1, pageSize: 100, isActive: true });
            const pages = Math.ceil(first.count / 100);
            const rest = await Promise.all(Array.from({ length: Math.max(0, pages - 1) }, (_, index) =>
                ingredientRepository.findAll({ page: index + 2, pageSize: 100, isActive: true }),
            ));
            return [...first.results, ...rest.flatMap((page) => page.results)];
        },
        enabled: Boolean(canCreate && userId && businessId),
    });

    const mutation = useMutation({
        mutationFn: () => createPurchaseRequisition.execute({
            reason: reason.trim(),
            items: lines.map((line) => ({
                ingredientId: line.ingredientId,
                quantity: line.quantity.trim(),
                note: line.note.trim(),
            })),
        }),
        onSuccess: async (saved) => {
            await queryClient.invalidateQueries({ queryKey: ['purchase-requisitions', userId, businessId] });
            navigate(`/purchase/requisitions/${saved.id}`);
        },
        onError: (error) => setFormError(errorMessage(error)),
    });

    const updateLine = (key: string, patch: Partial<DraftLine>) =>
        setLines((current) => current.map((line) => line.key === key ? { ...line, ...patch } : line));
    const submit = (event: FormEvent) => {
        event.preventDefault();
        setFormError('');
        mutation.mutate();
    };

    if (!canCreate) return <Container maxWidth="md" dir="rtl" sx={{ py: 3 }}><Alert severity="error">مجوز ایجاد درخواست خرید را ندارید.</Alert></Container>;

    return (
        <Container maxWidth="md" dir="rtl" sx={{ py: 3 }}>
            <Stack spacing={2.5}>
                <Box>
                    <Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>ایجاد درخواست خرید</Typography>
                    <Typography color="text.secondary">درخواست در ابتدا به‌صورت پیش‌نویس ثبت می‌شود؛ ارسال برای بررسی مرحله جداگانه‌ای است.</Typography>
                </Box>
                {ingredients.isLoading && <Box role="status" sx={{ display: 'flex', justifyContent: 'center', py: 4 }}><CircularProgress /></Box>}
                {ingredients.isError && <Alert severity="error" action={<Button color="inherit" onClick={() => { void ingredients.refetch(); }}>تلاش مجدد</Button>}>دریافت مواد اولیه ناموفق بود.</Alert>}
                {ingredients.data?.length === 0 && <Alert severity="warning">برای ایجاد درخواست، ابتدا ماده اولیه فعال ثبت کنید.</Alert>}
                {formError && <Alert severity="error" onClose={() => setFormError('')}>{formError}</Alert>}
                {!ingredients.isLoading && ingredients.data && <Paper component="form" onSubmit={submit} sx={{ p: { xs: 2, sm: 3 } }}>
                    <Stack spacing={2.5}>
                        <TextField label="دلیل درخواست" value={reason} onChange={(event) => setReason(event.target.value)} multiline minRows={2} disabled={mutation.isPending} />
                        <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
                            <Typography variant="h6">اقلام درخواست</Typography>
                            <Button type="button" onClick={() => setLines((current) => [...current, newLine()])} disabled={mutation.isPending}>افزودن قلم</Button>
                        </Stack>
                        {lines.map((line, index) => (
                            <Paper key={line.key} variant="outlined" sx={{ p: 2 }}>
                                <Stack spacing={1.5}>
                                    <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center' }}>
                                        <Typography sx={{ fontWeight: 700 }}>قلم {index + 1}</Typography>
                                        <Button color="error" size="small" type="button" disabled={lines.length === 1 || mutation.isPending} onClick={() => setLines((current) => current.filter((item) => item.key !== line.key))}>حذف</Button>
                                    </Stack>
                                    <TextField select required label="ماده اولیه" value={line.ingredientId} onChange={(event) => updateLine(line.key, { ingredientId: event.target.value })} disabled={mutation.isPending}>
                                        {ingredients.data.map((ingredient) => <MenuItem key={ingredient.id} value={ingredient.id}>{ingredient.name}{ingredient.sku ? ` — ${ingredient.sku}` : ''}</MenuItem>)}
                                    </TextField>
                                    <TextField required label="مقدار" value={line.quantity} onChange={(event) => updateLine(line.key, { quantity: event.target.value })} slotProps={{ htmlInput: { inputMode: 'decimal' } }} disabled={mutation.isPending} />
                                    <TextField label="یادداشت قلم" value={line.note} onChange={(event) => updateLine(line.key, { note: event.target.value })} disabled={mutation.isPending} />
                                </Stack>
                            </Paper>
                        ))}
                        <Stack direction="row" spacing={1}>
                            <Button type="submit" variant="contained" disabled={mutation.isPending || ingredients.isLoading || ingredients.data.length === 0}>
                                {mutation.isPending ? <CircularProgress size={20} color="inherit" /> : 'ایجاد پیش‌نویس'}
                            </Button>
                            <Button type="button" onClick={() => navigate('/purchase/requisitions')} disabled={mutation.isPending}>انصراف</Button>
                        </Stack>
                    </Stack>
                </Paper>}
            </Stack>
        </Container>
    );
};
