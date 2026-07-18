// src/presentation/hooks/menu/useMenu.ts

import { useQuery } from "@tanstack/react-query";
import { container } from "../../../data/di/container.ts";

export const useGetMenuById = (id: number) => {
    const { getMenuByIdUseCase } = container.menuContainer;

    return useQuery({
        queryKey: ["menus", id],

        queryFn: () => getMenuByIdUseCase.execute(id),

        enabled: !!id,
    });
};