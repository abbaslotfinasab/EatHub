import type {RecipeRepository} from "../../../repositories/product/RecipeRepository.ts";
import type {RecipeFilters} from "../../../objects/filters/RecipeFilters.ts";
import type {RecipeResult} from "../../../entities/product/RecipeResult.ts";


export class GetAllRecipeWithComponents {
    constructor(private recipeRepository:RecipeRepository) {}
    async execute(filters?: RecipeFilters): Promise<RecipeResult[]> {
        return this.recipeRepository.findAll(filters);
    }
}