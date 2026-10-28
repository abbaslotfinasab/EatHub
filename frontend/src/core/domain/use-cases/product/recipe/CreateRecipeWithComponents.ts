// core/application/use-cases/recipe/CreateRecipeWithComponents.ts
import type {RecipeRepository} from '../../../repositories/product/RecipeRepository';
import { RecipeFormSchema, type RecipeFormValues } from './RecipeFormSchema';

export const CreateRecipeSchema = RecipeFormSchema;
export type CreateRecipeInput = RecipeFormValues;

export class CreateRecipeWithComponents {
    constructor(private recipeRepo: RecipeRepository) {}

    async execute(input: CreateRecipeInput) {
        const validated = CreateRecipeSchema.parse(input);
        const { ingredients, outputs, ...recipeData } = validated;
        return this.recipeRepo.create(recipeData, ingredients, outputs);
    }
}
