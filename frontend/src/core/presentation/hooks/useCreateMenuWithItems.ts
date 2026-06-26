// presentation/hooks/useCreateMenuWithItems.ts
import {useMutation, useQueryClient} from '@tanstack/react-query';
import {createMenuWithItemsUseCase} from "../../data/di/menu.ts";
import type {MenuFormInput} from "../../domain/objects/forms/MenuFormInput.ts";

export const useCreateMenuWithItems = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (input: MenuFormInput) => {
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