// presentation/hooks/useCreateRecipe.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type {
    CreateRecipeInput
} from "../../domain/use-cases/product/recipe/CreateRecipeWithComponents.ts";
import {createRecipeUseCase} from "../../data/di/recipe.ts";

export const useCreateRecipe = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (input: CreateRecipeInput) =>
            createRecipeUseCase.execute(input),
        onSuccess: () => {
            // پس از ایجاد موفق، لیست رسپی‌ها را مجدداً بارگیری می‌کنیم
            queryClient.invalidateQueries({ queryKey: ['recipes'] });
        },
    });
};