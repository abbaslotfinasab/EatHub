import type {MaterialIngredient} from "./MaterialIngredient.ts";
import type {Material} from "./Material.ts";

export interface MaterialResult {
    material: Material;
    ingredients: MaterialIngredient[];
}