// presentation/hooks/useGetAllRecipes.ts
import { useQuery } from '@tanstack/react-query';
import { getAllRecipesUseCase } from "../../data/di/recipe";
import type {RecipeFilters} from "../../domain/objects/filters/RecipeFilters.ts";
import { useAuthStore } from "../store/auth.store";

export const useGetAllRecipes = (filters?: RecipeFilters) => {
    const me = useAuthStore((state) => state.me);
    return useQuery({
        queryKey: ['recipes', me?.id ?? null, me?.active_business?.id ?? null, filters],
        queryFn: () => getAllRecipesUseCase.execute(filters),
    });
};
