// domain/use-cases/ingredient/GetAllIngredients.ts
import type { Ingredient } from '../../../entities/inventory/Ingredient.ts';
import type { IngredientRepository, IngredientFilters } from '../../../repositories/inventory/IngredientRepository.ts';

export class GetAllIngredients {
    constructor(private ingredientRepository: IngredientRepository) {}

    async execute(filters?: IngredientFilters): Promise<Ingredient[]> {
        // می‌توانید اعتبارسنجی ساده روی فیلترها انجام دهید (مثلاً search خالی نادیده گرفته شود)
        return this.ingredientRepository.findAll(filters);
    }
}