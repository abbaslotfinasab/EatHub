// presentation/hooks/useCreateMaterial.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type {
    CreateMaterialWithIngredientsInput
} from "../../domain/use-cases/inventory/material/CreateMaterialWithIngredients.ts";
import {createMaterialUseCase} from "../../data/di/material.ts";

export const useCreateMaterial = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (input: CreateMaterialWithIngredientsInput) =>
            createMaterialUseCase.execute(input),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['materials'] });
        },
    });
};