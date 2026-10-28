import {useQuery} from "@tanstack/react-query";
import {container} from "../../../data/di/container.ts";
import {useAuthStore} from "../../store/auth.store";
import {orderQueryKeys} from "./orderQueryKeys.ts";

export const useGetOrderRefund = (orderId?: string, enabled = false) => {
    const {refundOrderUseCase} = container.orderContainer;
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);

    return useQuery({
        queryKey: orderQueryKeys.refund(userId, businessId, orderId),
        enabled: Boolean(orderId) && businessId !== null && enabled,
        queryFn: async () => {
            if (!orderId) return null;
            return refundOrderUseCase.getResult(orderId);
        },
        retry: false,
    });
};
