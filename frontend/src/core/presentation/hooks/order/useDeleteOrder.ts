import {useMutation, useQueryClient} from "@tanstack/react-query";
import {container} from "../../../data/di/container";
import {useAuthStore} from "../../store/auth.store";
import {invalidateOrderQueries} from "./invalidateOrderQueries";

export const useDeleteOrder = () => {
    const queryClient = useQueryClient();
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    const {deleteOrderUseCase} = container.orderContainer;

    return useMutation({
        mutationFn: async (id: string) => deleteOrderUseCase.execute(id),
        onMutate: () => ({userId, businessId}),
        onSuccess: async (_data, id, scope) => {
            await invalidateOrderQueries(queryClient, scope, id, "delete");
        },
        onError: (error) => {
            console.error("DELETE ORDER FAILED:", error);
        },
    });
};
