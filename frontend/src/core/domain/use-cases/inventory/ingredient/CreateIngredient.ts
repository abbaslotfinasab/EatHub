import { z } from 'zod';
import { Unit } from '../../../entities/inventory/Ingredient.ts';
import type { IngredientInput } from '../../../entities/inventory/Ingredient.ts';
import type { IngredientRepository } from '../../../repositories/inventory/IngredientRepository.ts';

export const CreateIngredientSchema = z.object({
    name: z.string().trim().min(1, 'نام ماده الزامی است').max(120),
    sku: z.string().trim().max(50).nullable().optional(),
    unit: z.enum(Unit),
    preparationLevel: z.enum(['raw', 'semi_prepared']).default('raw'),
    isActive: z.boolean().default(true),
});

export type CreateIngredientInput = z.input<typeof CreateIngredientSchema>;

export class CreateIngredient {
    constructor(private ingredientRepository: IngredientRepository) {}

    async execute(input: CreateIngredientInput) {
        const validated: IngredientInput = CreateIngredientSchema.parse(input);
        return this.ingredientRepository.create(validated);
    }
}
