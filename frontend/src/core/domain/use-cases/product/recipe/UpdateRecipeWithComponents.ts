// core/application/use-cases/recipe/UpdateRecipeWithComponents.ts
import {z} from 'zod';
import type {RecipeRepository} from '../../../repositories/product/RecipeRepository';
import type {RecipeResult} from "../../../entities/product/RecipeResult.ts";

// شِمای هر ماده مصرفی – فقط اعتبارسنجی سطحی (فقط نوع داده)
const UpdateRecipeIngredientItemSchema = z.object({
    recipeId: z.string(),
    ingredientId: z.string().nullable().optional(),
    materialId: z.string().nullable().optional(),
    quantity: z.number().positive(),
    substituteIngredientId: z.string().nullable().optional(),
    substituteMaterialId: z.string().nullable().optional(),
    // componentType وجود ندارد – بک‌اند آن را محاسبه می‌کند
});

// شمای اصلی ورودی
const UpdateRecipeSchema = z.object({
    yield: z.number().positive().optional(),
    instructions: z.string().nullable().optional(),
    description: z.string().nullable().optional(),
    ingredients: z.array(UpdateRecipeIngredientItemSchema)
});

export type UpdateRecipeInput = z.infer<typeof UpdateRecipeSchema>;

export class UpdateRecipeWithComponents {
    constructor(private recipeRepo: RecipeRepository) {}

    async execute(recipeId: string, input: UpdateRecipeInput): Promise<RecipeResult> {
        if (!recipeId) throw new Error('شناسه دستور پخت معتبر نیست');

        // فقط داده را اعتبارسنجی ساده کرده و همان‌طور که هست به ریپازیتوری می‌فرستیم
        const validated = UpdateRecipeSchema.parse(input);

        // جدا کردن ingredients از بقیه فیلدهای Recipe
        const { ingredients, ...recipeData } = validated;

        // ارسال به ریپازیتوری (بک‌اند تمام اعتبارسنجی‌های لازم را انجام می‌دهد)
        return await this.recipeRepo.update(recipeId, recipeData, ingredients);
    }
}