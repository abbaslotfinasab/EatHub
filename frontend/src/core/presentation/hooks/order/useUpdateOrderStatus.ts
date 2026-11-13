import {
    useMutation,
    useQueryClient,
} from "@tanstack/react-query";

import {container} from "../../../data/di/container";
import {useAuthStore} from "../../store/auth.store";
import {orderQueryKeys} from "./orderQueryKeys";

import type {UpdateOrderStatusInput} from "../../../domain/entities/product/order/UpdateOrderStatusInput";


export const useUpdateOrderStatus = () => {
    const queryClient = useQueryClient();
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);

    const {
        updateOrderStatusUseCase,
    } = container.orderContainer;

    return useMutation({
        mutationFn: async (
            input: UpdateOrderStatusInput,
        ) => updateOrderStatusUseCase.execute(input),

        onMutate: () => ({userId, businessId}),

        onSuccess: async (_data, input, scope) => {
            if (scope.businessId === null) return;

            await Promise.all([
                queryClient.invalidateQueries({
                    queryKey: orderQueryKeys.listPrefix(scope.userId, scope.businessId),
                }),
                queryClient.invalidateQueries({
                    queryKey: orderQueryKeys.detail(scope.userId, scope.businessId, input.orderId),
                    exact: true,
                }),
                queryClient.invalidateQueries({
                    queryKey: orderQueryKeys.statusHistory(scope.userId, scope.businessId, input.orderId),
                    exact: true,
                }),
                queryClient.invalidateQueries({
                    queryKey: orderQueryKeys.consumption(scope.userId, scope.businessId, input.orderId),
                    exact: true,
                }),
                queryClient.invalidateQueries({
                    queryKey: orderQueryKeys.refund(scope.userId, scope.businessId, input.orderId),
                    exact: true,
                }),
            ]);
        },

        onError: (error) => {
            console.error("UPDATE ORDER STATUS FAILED:", error);
        },
    });
};
