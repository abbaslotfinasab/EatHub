// presentation/hooks/useCreateMenu.ts

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { MenuFormMapper } from "../../forms/menu/MenuFormMapper.ts";

import type { MenuFormInput } from "../../forms/menu/MenuFormInput.ts";
import {container} from "../../../data/di/container.ts";

export const useCreateMenu = () => {
    const queryClient = useQueryClient();

    const { createMenuWithItemsUseCase } = container.menuContainer;

    return useMutation({
        mutationFn: async (input: MenuFormInput) => {
            const menu = MenuFormMapper.toDomain(input);

            return await createMenuWithItemsUseCase.execute(menu);
        },

        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: ["menus"],
            });
        },

        onError: (error) => {
            console.error("CREATE MENU FAILED:", error);
        },
    });
};