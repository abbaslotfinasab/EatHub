import {useMutation, useQueryClient} from "@tanstack/react-query";
import {container} from "../../../data/di/container.ts";
import {useAuthStore} from "../../store/auth.store";
import {orderQueryKeys} from "./orderQueryKeys.ts";
import type {RecordOrderConsumptionInput} from "../../../domain/entities/product/order/OrderInventoryConsumption.ts";

export const useRecordOrderConsumption = () => {
    const queryClient = useQueryClient();
    const useCase = container.orderContainer.recordOrderConsumptionUseCase;
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);

    return useMutation({
        mutationFn: (input: RecordOrderConsumptionInput) => useCase.execute(input),
        onMutate: () => ({userId, businessId}),
        onSuccess: async (_data, input, scope) => {
            if (scope.businessId === null) return;

            await Promise.all([
                queryClient.invalidateQueries({
                    queryKey: orderQueryKeys.detail(scope.userId, scope.businessId, input.orderId),
                    exact: true,
                }),
                queryClient.invalidateQueries({
                    queryKey: orderQueryKeys.consumption(scope.userId, scope.businessId, input.orderId),
                    exact: true,
                }),
            ]);
        },
    });
};
