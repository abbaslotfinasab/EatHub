import {useMutation, useQueryClient} from "@tanstack/react-query";
import {container} from "../../../data/di/container.ts";

export const useDeleteMenuItem = () => {
    const queryClient = useQueryClient();
    const {deleteMenuItemUseCase} = container.menuContainer;

    return useMutation({
        mutationFn: (id: number) => deleteMenuItemUseCase.execute(id),
        onSuccess: () => queryClient.invalidateQueries({queryKey: ["menus"]}),
    });
};
