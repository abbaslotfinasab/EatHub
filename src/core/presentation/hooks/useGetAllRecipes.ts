// presentation/hooks/useGetAllRecipes.ts
import { useQuery } from '@tanstack/react-query';
import { getAllRecipesUseCase } from "../../data/di/recipe";
import type {RecipeFilters} from "../../domain/objects/filters/RecipeFilters.ts";

export const useGetAllRecipes = (filters?: RecipeFilters) => {
    return useQuery({
        queryKey: ['recipes', filters],
        queryFn: () => getAllRecipesUseCase.execute(filters),
    });
};