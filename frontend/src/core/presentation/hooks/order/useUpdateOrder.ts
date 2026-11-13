import {useMutation, useQueryClient} from "@tanstack/react-query";

import {container} from "../../../data/di/container.ts";
import {OrderFormMapper} from "../../forms/order/OrderFormMapper.tsx";
import type {OrderFormInput} from "../../forms/order/OrderFormInput.ts";
import {useAuthStore} from "../../store/auth.store";
import {invalidateOrderQueries} from "./invalidateOrderQueries";

export interface UpdateOrderVariables {
    id: string;
    input: OrderFormInput;
}

export const useUpdateOrder = () => {
    const queryClient = useQueryClient();
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    const {updateOrderUseCase} = container.orderContainer;

    return useMutation({
        mutationFn: ({id, input}: UpdateOrderVariables) => {
            const order = OrderFormMapper.toDomain(input);
            return updateOrderUseCase.execute(id, order);
        },
        onMutate: () => ({userId, businessId}),
        onSuccess: async (_data, variables, scope) => {
            await invalidateOrderQueries(queryClient, scope, variables.id, "update");
        },
    });
};
