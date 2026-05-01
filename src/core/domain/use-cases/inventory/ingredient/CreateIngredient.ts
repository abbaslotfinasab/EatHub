// domain/use-cases/CreateIngredient.ts
import { z } from 'zod';
import { Unit } from '../../../entities/inventory/Ingredient.ts';
import type { IngredientRepository } from '../../../repositories/inventory/IngredientRepository.ts';

const CreateIngredientSchema = z.object({
    name: z.string().min(2, 'نام ماده حداقل ۲ کاراکتر است').trim(),
    unit: z.enum(Unit, { message: 'واحد معتبر نیست' }),
    currentStock: z.number().min(0).optional().default(0),
    reorderLevel: z.number().min(0),
    reorderQuantity: z.number().positive(),
    costPrice: z.number().positive(),
    isActive: z.boolean().optional().default(true),
    categoryId: z.string().nullable().optional(),
    supplierId: z.string().nullable().optional(),
    complete: z.boolean().optional().default(false),
    sku: z.string().nullable().optional(),
});

export type CreateIngredientInput = z.infer<typeof CreateIngredientSchema>;

export class CreateIngredient {
    constructor(private ingredientRepository: IngredientRepository) {}

    async execute(input: CreateIngredientInput): Promise<void> {
        // اعتبارسنجی ورودی
        const validated = CreateIngredientSchema.parse(input);

        // ارسال به ریپازیتوری (که درخواست POST به بک‌اند می‌دهد)
        await this.ingredientRepository.create(validated);
    }
}