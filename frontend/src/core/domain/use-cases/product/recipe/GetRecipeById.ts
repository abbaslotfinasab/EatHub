import type { RecipeRepository } from "../../../repositories/product/RecipeRepository";

export class GetRecipeById {
    constructor(private readonly recipeRepository: RecipeRepository) {}

    execute(id: string) {
        if (!id) throw new Error("شناسه رسپی معتبر نیست");
        return this.recipeRepository.findById(id);
    }
}
