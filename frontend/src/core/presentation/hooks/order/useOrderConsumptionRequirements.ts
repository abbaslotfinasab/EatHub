import {useQuery} from "@tanstack/react-query";
import {container} from "../../../data/di/container.ts";
import {useAuthStore} from "../../store/auth.store";
import {orderQueryKeys} from "./orderQueryKeys.ts";

export const useOrderConsumptionRequirements = (orderId?: string, enabled = true) => {
    const useCase = container.orderContainer.getOrderConsumptionRequirementsUseCase;
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    return useQuery({
        queryKey: orderQueryKeys.consumption(userId, businessId, orderId),
        enabled: Boolean(orderId) && businessId !== null && enabled,
        queryFn: () => {
            if (!orderId) throw new Error("شناسه سفارش معتبر نیست");
            return useCase.execute(orderId);
        },
    });
};
