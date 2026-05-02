// core/application/use-cases/materialIngredient/DeleteMaterialIngredient.ts
import type { MaterialIngredientRepository } from '../../../repositories/inventory/MaterialIngredientRepository';

export class DeleteMaterialIngredient {
    constructor(private readonly materialIngredientRepository: MaterialIngredientRepository) {}

    async execute(materialIngredientId: string): Promise<void> {
        if (!materialIngredientId) throw new Error('MaterialIngredient ID is required');
        // فقط یک درخواست DELETE به endpoint مربوطه می‌فرستد
        await this.materialIngredientRepository.delete(materialIngredientId);
    }
}