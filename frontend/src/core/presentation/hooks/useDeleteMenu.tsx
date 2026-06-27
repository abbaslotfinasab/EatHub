// hooks/menu/useDeleteMenu.ts

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { container } from "../../data/di/container";

export const useDeleteMenu = () => {
    const queryClient = useQueryClient();

    const { deleteMenuUseCase } = container.menuContainer;

    return useMutation({
        mutationFn: async (id: string) => {
            return await deleteMenuUseCase.execute(id);
        },

        onSuccess: (_, id) => {
            // 🔥 لیست منوها
            queryClient.invalidateQueries({
                queryKey: ["menus"],
            });

            // 🔥 اگر صفحه detail داری
            queryClient.invalidateQueries({
                queryKey: ["menus", id],
            });

            // 💡 (اختیاری ولی حرفه‌ای‌تر)
            queryClient.removeQueries({
                queryKey: ["menus", id],
            });
        },

        onError: (error) => {
            console.error("DELETE MENU FAILED:", error);
        },
    });
};