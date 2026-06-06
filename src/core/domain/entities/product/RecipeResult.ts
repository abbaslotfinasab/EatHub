import type {Recipe} from "./Recipe.ts";
import type {RecipeComponents} from "./RecipeComponents.ts";

export interface RecipeResult {
    recipe: Recipe;
    ingredients: RecipeComponents[];
}
