import {useMutation, useQueryClient} from "@tanstack/react-query";
import {container} from "../../../data/di/container";
import type {RefundOrderInput} from "../../../domain/entities/product/order/RefundOrderInput.ts";

export const useRefundOrder = () => {
    const queryClient = useQueryClient();
    const {refundOrderUseCase} = container.orderContainer;

    return useMutation({
        mutationFn: (input: RefundOrderInput) => refundOrderUseCase.execute(input),
        onSuccess: () => {
            queryClient.invalidateQueries({queryKey: ["orders"]});
        },
    });
};
