import { z } from 'zod';
import { Unit } from '../../../entities/inventory/Ingredient.ts';
import type { Ingredient, IngredientInput } from '../../../entities/inventory/Ingredient.ts';
import type { IngredientRepository } from '../../../repositories/inventory/IngredientRepository.ts';

export const UpdateIngredientSchema = z.object({
    name: z.string().trim().min(1).max(120).optional(),
    sku: z.string().trim().max(50).nullable().optional(),
    unit: z.enum(Unit).optional(),
    preparationLevel: z.enum(['raw', 'semi_prepared']).optional(),
    isActive: z.boolean().optional(),
});

export type UpdateIngredientInput = z.input<typeof UpdateIngredientSchema>;

export class UpdateIngredient {
    constructor(private ingredientRepository: IngredientRepository) {}

    async execute(id: string, input: UpdateIngredientInput): Promise<Ingredient> {
        if (!id.trim()) throw new Error('شناسه معتبر نیست');
        return this.ingredientRepository.update(id, UpdateIngredientSchema.parse(input) as Partial<IngredientInput>);
    }
}
