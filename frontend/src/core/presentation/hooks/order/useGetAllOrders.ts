import { useQuery } from "@tanstack/react-query";
import {container} from "../../../data/di/container.ts";


export const useGetAllOrders = () => {
    const { getAllOrdersUseCase } = container.orderContainer;

    return useQuery({
        queryKey: ["orders"],
        queryFn: async () => {
            try {
                return await getAllOrdersUseCase.execute();
            } catch (error) {
                console.error("GET ORDERS FAILED:", error);
                throw error;
            }
        },
    });
};