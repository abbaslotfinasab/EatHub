// presentation/hooks/useCreateIngredient.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type {CreateIngredientInput} from "../../domain/use-cases/inventory/ingredient/CreateIngredient.ts";
import {createIngredientUseCase} from "../../data/di/ingredient.ts";

export const useCreateIngredient = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (input: CreateIngredientInput) =>
            createIngredientUseCase.execute(input),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['ingredients'] });
        },
    });
};