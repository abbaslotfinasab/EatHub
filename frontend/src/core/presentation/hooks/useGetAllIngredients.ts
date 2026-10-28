// presentation/hooks/useGetAllIngredients.ts
import { useQuery } from '@tanstack/react-query';
import {getAllIngredientsUseCase} from "../../data/di/ingredient.ts";
import type {IngredientFilters} from "../../domain/repositories/inventory/IngredientRepository.ts";
import { useAuthStore } from "../store/auth.store";

export const useGetAllIngredients = (filters?: IngredientFilters) => {
    const me = useAuthStore((state) => state.me);
    return useQuery({
        queryKey: ['ingredients', me?.id ?? null, me?.active_business?.id ?? null, filters],
        queryFn: () => getAllIngredientsUseCase.execute(filters),
    });
};
