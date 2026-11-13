import {useMutation, useQueryClient} from "@tanstack/react-query";

import {container} from "../../../data/di/container";
import {useAuthStore} from "../../store/auth.store";
import {invalidateOrderQueries} from "./invalidateOrderQueries";

import type {UpdateOrderStatusInput} from "../../../domain/entities/product/order/UpdateOrderStatusInput";

export const useUpdateOrderStatus = () => {
    const queryClient = useQueryClient();
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    const {updateOrderStatusUseCase} = container.orderContainer;

    return useMutation({
        mutationFn: (input: UpdateOrderStatusInput) => updateOrderStatusUseCase.execute(input),
        onMutate: () => ({userId, businessId}),
        onSuccess: async (_data, input, scope) => {
            await invalidateOrderQueries(queryClient, scope, input.orderId, "status");
        },
        onError: (error) => {
            console.error("UPDATE ORDER STATUS FAILED:", error);
        },
    });
};
