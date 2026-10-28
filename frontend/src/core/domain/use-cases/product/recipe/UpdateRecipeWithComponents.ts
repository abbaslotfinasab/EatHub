// core/application/use-cases/recipe/UpdateRecipeWithComponents.ts
import type {RecipeRepository} from '../../../repositories/product/RecipeRepository';
import type {RecipeResult} from "../../../entities/product/RecipeResult.ts";
import { RecipeFormSchema, type RecipeFormValues } from './RecipeFormSchema';

export const UpdateRecipeSchema = RecipeFormSchema;
export type UpdateRecipeInput = RecipeFormValues;

export class UpdateRecipeWithComponents {
    constructor(private recipeRepo: RecipeRepository) {}

    async execute(recipeId: string, input: UpdateRecipeInput): Promise<RecipeResult> {
        if (!recipeId) throw new Error('شناسه دستور پخت معتبر نیست');

        const validated = UpdateRecipeSchema.parse(input);
        const { ingredients, outputs, ...recipeData } = validated;
        return this.recipeRepo.update(recipeId, recipeData, ingredients, outputs);
    }
}
