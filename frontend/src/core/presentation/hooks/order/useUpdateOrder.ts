import { useMutation, useQueryClient } from "@tanstack/react-query";

import {container} from "../../../data/di/container.ts";
import {OrderFormMapper} from "../../forms/order/OrderFormMapper.tsx";
import type {OrderFormInput} from "../../forms/order/OrderFormInput.ts";

export interface UpdateOrderVariables {
    id: string;
    input: OrderFormInput;
}
export const useUpdateOrder = () => {
    const queryClient = useQueryClient();

    const { updateOrderUseCase } = container.orderContainer;

    return useMutation({
        mutationFn: ({ id, input }: UpdateOrderVariables) => {

            const order =
                OrderFormMapper.toDomain(input);

            return updateOrderUseCase.execute(
                id,
                order,
            );
        },

        onSuccess: (_, variables) => {

            queryClient.invalidateQueries({
                queryKey: ["orders"],
            });

            queryClient.invalidateQueries({
                queryKey: [
                    "orders",
                    variables.id,
                ],
            });

        },
    });
};