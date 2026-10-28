import { useState, type FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Alert, Box, Button, CircularProgress, Container, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material';
import { createIngredientUseCase, getIngredientByIdUseCase, updateIngredientUseCase } from '../../data/di/ingredient.ts';
import { Unit, type UnitType } from '../../domain/entities/inventory/Ingredient.ts';
import type { Ingredient, IngredientInput } from '../../domain/entities/inventory/Ingredient.ts';
import { useAuthStore } from '../store/auth.store';

const errorText = (error: unknown) => {
    const response = (error as { response?: { status?: number; data?: unknown } })?.response;
    if (response?.status === 403) return 'اجازه مدیریت مواد اولیه را ندارید.';
    if (response?.data) return JSON.stringify(response.data);
    return error instanceof Error ? error.message : 'خطای ارتباط با سرور.';
};
const unitLabel = (unit: string) => ({ kg: 'کیلوگرم', g: 'گرم', l: 'لیتر', ml: 'میلی‌لیتر', pc: 'عدد', pk: 'بسته' }[unit as UnitType] ?? unit);

export const CreateIngredientPage = () => {
    const { id } = useParams();
    const me = useAuthStore((state) => state.me);
    const itemQuery = useQuery({
        queryKey: ['ingredient', me?.id ?? null, me?.active_business?.id ?? null, id],
        queryFn: () => getIngredientByIdUseCase.execute(id!),
        enabled: Boolean(id),
    });

    if (id && itemQuery.isLoading) return <Box role="status" sx={{ display: 'flex', justifyContent: 'center', py: 8 }}><CircularProgress /></Box>;
    if (id && (itemQuery.isError || !itemQuery.data)) return <Alert severity="error">دریافت ماده اولیه ناموفق بود. {errorText(itemQuery.error)}</Alert>;

    return <IngredientEditor key={id ?? 'new'} initial={itemQuery.data ?? undefined} />;
};

const IngredientEditor = ({ initial }: { initial?: Ingredient }) => {
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [form, setForm] = useState<IngredientInput>(() => ({
        name: initial?.name ?? '',
        sku: initial?.sku ?? '',
        unit: initial?.unit ?? Unit.KG,
        preparationLevel: 'raw',
        isActive: initial?.isActive ?? true,
    }));
    const create = useMutation({
        mutationFn: (input: IngredientInput) => createIngredientUseCase.execute(input),
        onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ['ingredients'] }); navigate('/ingredients'); },
    });
    const update = useMutation({
        mutationFn: (input: Partial<IngredientInput>) => updateIngredientUseCase.execute(initial!.id, input),
        onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ['ingredients'] }); navigate('/ingredients'); },
    });
    const mutationError = create.error ?? update.error;

    const submit = (event: FormEvent) => {
        event.preventDefault();
        if (initial) update.mutate(form);
        else create.mutate(form);
    };

    return (
        <Container maxWidth="md" sx={{ py: 2 }} dir="rtl">
            <Paper component="form" onSubmit={submit} sx={{ p: 3 }}>
                <Stack spacing={2.5}>
                    <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>{initial ? 'ویرایش ماده اولیه' : 'ماده اولیه جدید'}</Typography>
                    {mutationError && <Alert severity="error">{errorText(mutationError)}</Alert>}
                    <TextField required label="نام" slotProps={{ htmlInput: { maxLength: 120 } }} value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
                    <TextField label="SKU" slotProps={{ htmlInput: { maxLength: 50 } }} value={form.sku ?? ''} onChange={(event) => setForm({ ...form, sku: event.target.value })} helperText="در هر کسب‌وکار یکتا است؛ حروف بزرگ و کوچک متمایز هستند." />
                    <TextField select label="واحد پایه" value={form.unit} onChange={(event) => setForm({ ...form, unit: event.target.value as IngredientInput['unit'] })}>
                        {Object.values(Unit).map((unit) => <MenuItem key={unit} value={unit}>{unitLabel(unit)}</MenuItem>)}
                    </TextField>
                    <label><input type="checkbox" checked={form.isActive ?? true} onChange={(event) => setForm({ ...form, isActive: event.target.checked })} /> فعال</label>
                    <Stack direction="row" spacing={1}>
                        <Button type="submit" variant="contained" disabled={create.isPending || update.isPending}>{initial ? 'ذخیره تغییرات' : 'ایجاد ماده'}</Button>
                        <Button type="button" onClick={() => navigate('/ingredients')}>بازگشت</Button>
                    </Stack>
                </Stack>
            </Paper>
        </Container>
    );
};
