import {useMutation, useQueryClient} from "@tanstack/react-query";
import {container} from "../../../data/di/container";
import type {RefundOrderInput} from "../../../domain/entities/product/order/RefundOrderInput.ts";

export const useRefundOrder = () => {
    const queryClient = useQueryClient();
    const {refundOrderUseCase} = container.orderContainer;

    return useMutation({
        mutationFn: (input: RefundOrderInput) => refundOrderUseCase.execute(input),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({queryKey: ["orders"]});
            queryClient.invalidateQueries({queryKey: ["orders", variables.orderId]});
            queryClient.invalidateQueries({queryKey: ["orders", variables.orderId, "refund"]});
        },
    });
};
