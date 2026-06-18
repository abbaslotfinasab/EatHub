// presentation/hooks/useDeleteIngredient.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {deleteIngredientUseCase} from "../../data/di/ingredient.ts";

export const useDeleteIngredient = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => deleteIngredientUseCase.execute(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['ingredients'] });
        },
    });
};