import {useQuery} from "@tanstack/react-query";
import {container} from "../../../data/di/container.ts";

export const useGetOrderRefund = (orderId?: string, enabled = false) => {
    const {refundOrderUseCase} = container.orderContainer;

    return useQuery({
        queryKey: ["orders", orderId, "refund"],
        enabled: Boolean(orderId) && enabled,
        queryFn: async () => {
            if (!orderId) return null;
            return refundOrderUseCase.getResult(orderId);
        },
        retry: false,
    });
};
