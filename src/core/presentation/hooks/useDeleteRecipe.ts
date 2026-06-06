// presentation/hooks/useDeleteRecipe.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {deleteRecipeUseCase} from "../../data/di/recipe.ts";

export const useDeleteRecipe = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => deleteRecipeUseCase.execute(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['recipes'] });
        },
    });
};