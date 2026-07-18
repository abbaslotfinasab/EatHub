import { useMutation, useQueryClient } from "@tanstack/react-query";
import { container } from "../../../data/di/container";


export const useDeleteOrder = () => {
    const queryClient = useQueryClient();

    const { deleteOrderUseCase } = container.orderContainer;

    return useMutation({
        mutationFn: async (id: string) => {
            return await deleteOrderUseCase.execute(id);
        },

        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: ["orders"],
            });
        },

        onError: (error) => {
            console.error("DELETE ORDER FAILED:", error);
        },
    });
};