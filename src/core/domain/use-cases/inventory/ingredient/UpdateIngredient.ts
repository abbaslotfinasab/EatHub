// domain/use-cases/ingredient/UpdateIngredient.ts (پیشرفته)
import { z } from 'zod';
import { Unit } from '../../../entities/inventory/Ingredient.ts';
import type { Ingredient } from '../../../entities/inventory/Ingredient.ts';
import type { IngredientRepository } from '../../../repositories/inventory/IngredientRepository.ts';

const UpdateIngredientSchema = z.object({
    name: z.string().min(2).trim().optional(),
    unit: z.enum(Unit).optional(),
    currentStock: z.number().min(0).optional(),
    reorderLevel: z.number().min(0).optional(),
    reorderQuantity: z.number().positive().optional(),
    costPrice: z.number().positive().optional(),
    isActive: z.boolean().optional(),
    categoryId: z.string().nullable().optional(),
    supplierId: z.string().nullable().optional(),
    complete: z.boolean().optional(),
});

export type UpdateIngredientInput = z.infer<typeof UpdateIngredientSchema>;

export class UpdateIngredient {
    constructor(private ingredientRepository: IngredientRepository) {}

    async execute(id: string, input: UpdateIngredientInput): Promise<Ingredient> {
        if (!id) throw new Error('شناسه معتبر نیست');

        // اعتبارسنجی ورودی
        const validated = UpdateIngredientSchema.parse(input);

        // (اختیاری) می‌توانید بررسی کنید که آیا ماده وجود دارد یا نه
        const existing = await this.ingredientRepository.findById(id);
        if (!existing) {
            throw new Error('ماده اولیه یافت نشد');
        }

        // ارسال درخواست و برگرداندن ماده به‌روز شده (ریپازیتوری باید Promise<Ingredient> برگرداند)
        return this.ingredientRepository.update(id, validated);
    }
}