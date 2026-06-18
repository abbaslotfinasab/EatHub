// core/application/use-cases/material/CreateMaterialWithIngredients.ts
import { z } from 'zod';
import type { MaterialRepository } from '../../../repositories/inventory/MaterialRepository';

// شِمای هر آیتم MaterialIngredient
const MaterialIngredientItemSchema = z.object({
    ingredientId: z.string().min(1, 'شناسه ماده اولیه مصرفی الزامی است'),
    quantity: z.number().positive('مقدار مصرف باید مثبت باشد'),
    unit: z.string(),
    substituteMaterialId: z.string().nullable().optional(),
});

// شمای اصلی شامل Material و لیست مواد مصرفی
export const CreateMaterialWithIngredientsSchema = z.object({
    name: z.string().min(2).trim(),
    description: z.string().nullable(),
    unitId: z.string(),
    currentStock: z.number().min(0).default(0),
    reorderLevel: z.number().min(0),
    reorderQuantity: z.number().positive(),
    costPrice: z.number().positive().default(0),
    ingredients: z.array(MaterialIngredientItemSchema).min(1, 'حداقل یک ماده مصرفی الزامی است'),
});

export type CreateMaterialWithIngredientsInput = z.infer<typeof CreateMaterialWithIngredientsSchema>;

export class CreateMaterialWithIngredients {
    constructor(private materialRepository: MaterialRepository) {}

    async execute(input: CreateMaterialWithIngredientsInput) {
        const validated = CreateMaterialWithIngredientsSchema.parse(input);

        const { ingredients, ...materialData } = validated;


        // ارسال به ریپازیتوری (بک‌اند در یک تراکنش ذخیره می‌کند)
        return await this.materialRepository.creat(materialData,ingredients);
    }
}