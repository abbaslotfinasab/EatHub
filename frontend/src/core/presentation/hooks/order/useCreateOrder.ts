import { useMutation, useQueryClient } from "@tanstack/react-query";
import {container} from "../../../data/di/container.ts";
import type {OrderFormInput} from "../../forms/order/OrderFormInput.ts";
import {OrderFormMapper} from "../../forms/order/OrderFormMapper.tsx";



export const useCreateOrder = () => {
    const queryClient = useQueryClient();

    const { createOrderUseCase } = container.orderContainer;

    return useMutation({
        mutationFn: async (input: OrderFormInput) => {
            return await createOrderUseCase.execute(OrderFormMapper.toDomain(input));
        },

        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: ["orders"],
            });
        },

        onError: (error) => {
            console.error("CREATE ORDER FAILED:", error);
        },
    });
};