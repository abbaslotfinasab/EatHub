// core/application/use-cases/recipe/CreateRecipeWithComponents.ts
import {z} from 'zod';
import type {RecipeRepository} from '../../../repositories/product/RecipeRepository';

const RecipeIngredientItemSchema = z.object({
    ingredientId: z.string(),
    materialId: z.string().nullable().optional(),
    quantity: z.number().positive(),
    unit: z.string().min(1),
    substituteIngredientId: z.string().nullable().optional(),
    substituteMaterialId: z.string().nullable().optional(),
}).refine(data => (data.ingredientId && !data.materialId) || (!data.ingredientId && data.materialId), {
    message: 'Exactly one of ingredientId or materialId must be provided',
});

export const CreateRecipeSchema = z.object({
    name: z.string().nullable().optional(),
    description: z.string().nullable().optional(),
    instructions: z.string().nullable().optional(),
    ingredients: z.array(RecipeIngredientItemSchema).min(1, 'حداقل یک ماده مصرفی باید وجود داشته باشد'),
});

export type CreateRecipeInput = z.infer<typeof CreateRecipeSchema>;

export class CreateRecipeWithComponents {
    constructor(private recipeRepo: RecipeRepository) {}

    async execute(input: CreateRecipeInput) {
        const validated = CreateRecipeSchema.parse(input);

        // جدا کردن ingredients از بقیه فیلدهای Recipe
        const { ingredients, ...recipeData } = validated;


        await this.recipeRepo.create(recipeData, ingredients);
    }
}