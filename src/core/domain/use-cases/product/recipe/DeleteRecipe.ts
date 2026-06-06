// core/application/use-cases/recipe/DeleteRecipe.ts
import type { RecipeRepository } from '../../../repositories/product/RecipeRepository';

export class DeleteRecipe {
    constructor(private recipeRepo: RecipeRepository) {}

    async execute(recipeId: string): Promise<void> {
        if (!recipeId) throw new Error('شناسه دستور پخت معتبر نیست');
        await this.recipeRepo.delete(recipeId); // حذف آبشاری
    }
}