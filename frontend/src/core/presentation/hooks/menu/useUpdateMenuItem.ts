import {useMutation, useQueryClient} from "@tanstack/react-query";
import {container} from "../../../data/di/container.ts";
import type {MenuItem} from "../../../domain/entities/product/menu/MenuItem.ts";

export interface UpdateMenuItemVariables {
    id: number;
    input: Partial<MenuItem>;
}

export const useUpdateMenuItem = () => {
    const queryClient = useQueryClient();
    const {updateMenuItemUseCase} = container.menuContainer;

    return useMutation({
        mutationFn: ({id, input}: UpdateMenuItemVariables) => updateMenuItemUseCase.execute(id, input),
        onSuccess: () => queryClient.invalidateQueries({queryKey: ["menus"]}),
    });
};
