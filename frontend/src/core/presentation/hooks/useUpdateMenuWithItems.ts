// hooks/menu/useUpdateMenu.ts

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { container } from "../../data/di/container";
import type {MenuFormInput} from "../../domain/objects/forms/MenuFormInput.ts";


export interface UpdateMenuVariables {
    id: string;
    input: MenuFormInput;
}

export const useUpdateMenuWithItems = () => {
    const queryClient = useQueryClient();

    const { updateMenuWithItemsUseCase } = container.menuContainer;

    return useMutation({
        mutationFn: ({ id, input }: UpdateMenuVariables) =>
            updateMenuWithItemsUseCase.execute(id, input),

        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({
                queryKey: ["menus"],
            });

            queryClient.invalidateQueries({
                queryKey: ["menus", variables.id],
            });
        },
    });
};