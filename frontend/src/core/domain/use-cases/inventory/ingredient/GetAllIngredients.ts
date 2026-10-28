// domain/use-cases/ingredient/GetAllIngredients.ts
import type { IngredientRepository, IngredientFilters } from '../../../repositories/inventory/IngredientRepository.ts';

export class GetAllIngredients {
    constructor(private ingredientRepository: IngredientRepository) {}

    async execute(filters?: IngredientFilters) {
        // می‌توانید اعتبارسنجی ساده روی فیلترها انجام دهید (مثلاً search خالی نادیده گرفته شود)
        return this.ingredientRepository.findAll(filters);
    }
}
