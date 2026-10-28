import { useQuery } from "@tanstack/react-query";
import { getRecipeByIdUseCase } from "../../data/di/recipe";

export const useGetRecipe = (id: string) => useQuery({
    queryKey: ["recipe", id],
    queryFn: () => getRecipeByIdUseCase.execute(id),
    enabled: Boolean(id),
});
