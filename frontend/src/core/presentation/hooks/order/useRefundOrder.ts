import {useMutation, useQueryClient} from "@tanstack/react-query";
import {container} from "../../../data/di/container";
import type {RefundOrderInput} from "../../../domain/entities/product/order/RefundOrderInput.ts";
import {useAuthStore} from "../../store/auth.store";
import {invalidateOrderQueries} from "./invalidateOrderQueries";

export const useRefundOrder = () => {
    const queryClient = useQueryClient();
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    const {refundOrderUseCase} = container.orderContainer;

    return useMutation({
        mutationFn: (input: RefundOrderInput) => refundOrderUseCase.execute(input),
        onMutate: () => ({userId, businessId}),
        onSuccess: async (_data, input, scope) => {
            await invalidateOrderQueries(queryClient, scope, input.orderId, {
                list: true,
                detail: true,
                statusHistory: true,
                refund: true,
            });
        },
    });
};
