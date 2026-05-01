// domain/use-cases/ingredient/GetIngredientById.ts
import type { Ingredient } from '../../../entities/inventory/Ingredient.ts';
import type { IngredientRepository } from '../../../repositories/inventory/IngredientRepository.ts';

export class GetIngredientById {
    constructor(private ingredientRepository: IngredientRepository) {}

    async execute(id: string): Promise<Ingredient | null> {
        if (!id || id.trim() === '') {
            throw new Error('شناسه ماده اولیه معتبر نیست');
        }
        return this.ingredientRepository.findById(id);
    }
}