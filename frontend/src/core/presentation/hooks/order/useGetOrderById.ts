import { useQuery } from "@tanstack/react-query";
import {container} from "../../../data/di/container.ts";
import {useAuthStore} from "../../store/auth.store";
import {orderQueryKeys} from "./orderQueryKeys.ts";


export const useGetOrderById = (id?: string) => {
    const { getOrderByIdUseCase } = container.orderContainer;
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);

    return useQuery({
        queryKey: orderQueryKeys.detail(userId, businessId, id),

        enabled: Boolean(id) && businessId !== null,

        queryFn: async () => {
            if (!id) return null;

            try {
                return await getOrderByIdUseCase.execute(id);
            } catch (error) {
                console.error("GET ORDER FAILED:", error);
                throw error;
            }
        },
    });
};
