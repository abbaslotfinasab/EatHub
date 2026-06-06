// presentation/hooks/useGetAllIngredients.ts
import { useQuery } from '@tanstack/react-query';
import {getAllIngredientsUseCase} from "../../data/di/ingredient.ts";
import type {IngredientFilters} from "../../domain/repositories/inventory/IngredientRepository.ts";

export const useGetAllIngredients = (filters?: IngredientFilters) => {
    return useQuery({
        queryKey: ['ingredients', filters],
        queryFn: () => getAllIngredientsUseCase.execute(filters),
    });
};