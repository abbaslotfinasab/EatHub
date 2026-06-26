// src/presentation/hooks/menu/useMenu.ts

import { useQuery } from "@tanstack/react-query";
import { container } from "../../data/di/container";

export const useGetMenuById = (id: string) => {
    const { getMenuByIdUseCase } = container.menuContainer;

    return useQuery({
        queryKey: ["menus", id],

        queryFn: () => getMenuByIdUseCase.execute(id),

        enabled: !!id,
    });
};