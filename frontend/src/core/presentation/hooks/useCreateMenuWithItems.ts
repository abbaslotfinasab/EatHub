// presentation/hooks/useCreateMenuWithItems.ts
import {useMutation, useQueryClient} from '@tanstack/react-query';
import {createMenuWithItemsUseCase} from "../../data/di/menu.ts";
import type {CreateMenuWithItemsInput} from "../../domain/use-cases/product/menu/CreateMenuWithItems.ts";

export const useCreateMenuWithItems = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (input: CreateMenuWithItemsInput) => {
            return await createMenuWithItemsUseCase.execute(input);
        },

        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['menus'] });
        },

        onError: (error) => {
            console.error("CREATE MENU FAILED:", error);
        },
    });
};