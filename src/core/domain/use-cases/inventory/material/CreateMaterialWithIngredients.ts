// core/application/use-cases/material/CreateMaterialWithIngredients.ts
import { z } from 'zod';
import { Unit } from '../../../entities/inventory/Material';
import type { MaterialRepository } from '../../../repositories/inventory/MaterialRepository';
import type { MaterialIngredientRepository } from '../../../repositories/inventory/MaterialIngredientRepository.ts';
import type { Material } from '../../../entities/inventory/Material';
import type { MaterialIngredient } from '../../../entities/inventory/MaterialIngredient.ts';

// شِمای مربوط به هر آیتم MaterialIngredient که قرار است همراه Material ساخته شود
const MaterialIngredientItemSchema = z.object({
    ingredientId: z.string().min(1, 'شناسه ماده اولیه مصرفی الزامی است'),
    quantity: z.number().positive('مقدار مصرف باید مثبت باشد'),
    unit: z.enum(Unit),
    substituteMaterialId: z.string().nullable().optional(),
});

// شمای اصلی ورودی
const CreateMaterialWithIngredientsSchema = z.object({
    // فیلدهای Material
    name: z.string().min(2).trim(),
    description: z.string().nullable().optional(),
    unit: z.enum(Unit),
    currentStock: z.number().min(0).optional().default(0),
    reorderLevel: z.number().min(0),
    reorderQuantity: z.number().positive(),
    // لیست مواد مصرفی (MaterialIngredient)
    ingredients: z.array(MaterialIngredientItemSchema).optional().default([]),
});

export type CreateMaterialWithIngredientsInput = z.infer<typeof CreateMaterialWithIngredientsSchema>;

export class CreateMaterialWithIngredients {
    constructor(
        private materialRepository: MaterialRepository,
        private materialIngredientRepository: MaterialIngredientRepository,
    ) {}

    async execute(input: CreateMaterialWithIngredientsInput): Promise<{
        material: Material;
        ingredients: MaterialIngredient[];
    }> {
        // 1. اعتبارسنجی ورودی
        const validated = CreateMaterialWithIngredientsSchema.parse(input);

        // توجه: فرض می‌کنیم متد save ریپازیتوری، شیء ساخته شده را برمی‌گرداند
        const createdMaterial = await this.materialRepository.create(validated);

        // 4. ایجاد MaterialIngredientها برای material ساخته شده
        const createdIngredients: MaterialIngredient[] = [];
        for (const ing of validated.ingredients) {
            const ingredientData = {
                ingredientId: ing.ingredientId,
                quantity: ing.quantity,
                unit: ing.unit,
                substituteMaterialId: ing.substituteMaterialId ?? null,
            };
            const saved = await this.materialIngredientRepository.create(ingredientData as unknown as MaterialIngredient);
            createdIngredients.push(saved);
        }

        return {
            material: createdMaterial,
            ingredients: createdIngredients,
        };
    }
}