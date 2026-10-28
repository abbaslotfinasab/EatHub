import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateRecipeUseCase } from "../../data/di/recipe";
import type { UpdateRecipeInput } from "../../domain/use-cases/product/recipe/UpdateRecipeWithComponents";

export const useUpdateRecipe = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, values }: { id: string; values: UpdateRecipeInput }) =>
            updateRecipeUseCase.execute(id, values),
        onSuccess: (recipe) => {
            queryClient.setQueryData(["recipe", recipe.recipe.id], recipe);
            queryClient.invalidateQueries({ queryKey: ["recipes"] });
        },
    });
};
