// hooks/menu/useUpdateMenu.ts

import {useMutation, useQueryClient} from "@tanstack/react-query";
import {container} from "../../../data/di/container.ts";
import type {MenuFormInput} from "../../forms/menu/MenuFormInput.ts";
import {MenuFormMapper} from "../../forms/menu/MenuFormMapper.ts";


export interface UpdateMenuVariables {
    id: string;
    input: MenuFormInput;
}

export const useUpdateMenuWithItems = () => {
    const queryClient = useQueryClient();

    const {updateMenuWithItemsUseCase} = container.menuContainer;

    return useMutation({
        mutationFn: (variables: UpdateMenuVariables) => {
            const menu = MenuFormMapper.toDomain(variables.input);

            menu.menu.id = Number(variables.id);

            return updateMenuWithItemsUseCase.execute(menu);
        },

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