// presentation/hooks/menu/useGetMenus.ts

import { useQuery } from "@tanstack/react-query";
import {container} from "../../../data/di/container.ts";

export const useGetMenus = () => {
    const { getAllMenusUseCase } = container.menuContainer;

    return useQuery({
        queryKey: ["menus"],
        queryFn: async () => {
            try {
                const res = await getAllMenusUseCase.execute();
                console.log("MENUS RESPONSE:", res);
                return res;
            } catch (e) {
                console.error("USECASE ERROR:", e);
                throw e;
            }
        },
    });
};