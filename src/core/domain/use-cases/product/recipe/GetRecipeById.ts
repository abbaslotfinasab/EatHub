// core/application/use-cases/recipe/GetRecipeById.ts
import type { RecipeRepository } from '../../../repositories/product/RecipeRepository';

export class GetRecipeById {
    constructor(private recipeRepo: RecipeRepository) {}

    async execute(id: string) {
        if (!id) throw new Error('شناسه دستور پخت معتبر نیست');
        return this.recipeRepo.findById(id);
    }
}