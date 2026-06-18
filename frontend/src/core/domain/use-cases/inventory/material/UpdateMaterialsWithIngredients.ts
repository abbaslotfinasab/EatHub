// core/application/use-cases/material/UpdateMaterialWithIngredients.ts
import { z } from 'zod';
import type { MaterialRepository } from '../../../repositories/inventory/MaterialRepository';

// شِمای هر آیتم مصرفی (برای جایگزینی کامل)
const MaterialIngredientUpdateSchema = z.object({
    ingredientId: z.string().min(1, 'شناسه ماده اولیه مصرفی الزامی است'),
    quantity: z.number().positive('مقدار مصرف باید مثبت باشد'),
    unit: z.string(),
    substituteMaterialId: z.string().nullable().optional(),
});

// شمای اصلی ورودی
const UpdateMaterialWithIngredientsSchema = z.object({
    materialData: z.object({
        name: z.string().min(2).trim().optional(),
        description: z.string().nullable().optional(),
        unit: z.string(),
        currentStock: z.number().min(0).optional(),
        reorderLevel: z.number().min(0).optional(),
        reorderQuantity: z.number().positive().optional(),
        costPrice: z.number().positive().optional(),
    }),
    ingredients: z.array(MaterialIngredientUpdateSchema).optional(), // در صورت ارسال، جایگزین کامل آیتم‌های قبلی می‌شود
});

export type UpdateMaterialWithIngredientsInput = z.infer<typeof UpdateMaterialWithIngredientsSchema>;

export class UpdateMaterialWithIngredients {
    constructor(private materialRepository: MaterialRepository) {}

    async execute(materialId: string, input: UpdateMaterialWithIngredientsInput) {
        if (!materialId) throw new Error('شناسه ماده معتبر نیست');
        const validated = UpdateMaterialWithIngredientsSchema.parse(input);

        // استخراج data و ingredients
        const { materialData, ingredients } = validated;

        // ارسال به ریپازیتوری (بک‌اند اعتبارسنجی و جایگزینی آیتم‌ها را انجام می‌دهد)
        return await this.materialRepository.update(materialId, materialData, ingredients);
    }
}