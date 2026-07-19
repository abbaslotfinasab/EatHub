import { useQuery } from "@tanstack/react-query";
import {container} from "../../../data/di/container.ts";


export const useGetOrderById = (id?: string) => {
    const { getOrderByIdUseCase } = container.orderContainer;

    return useQuery({
        queryKey: ["orders", id],

        enabled: !!id,

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