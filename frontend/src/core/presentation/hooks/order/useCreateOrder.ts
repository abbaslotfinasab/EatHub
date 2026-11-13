import {useMutation, useQueryClient} from "@tanstack/react-query";
import {container} from "../../../data/di/container.ts";
import type {OrderFormInput} from "../../forms/order/OrderFormInput.ts";
import {OrderFormMapper} from "../../forms/order/OrderFormMapper.tsx";
import {useAuthStore} from "../../store/auth.store";
import {invalidateOrderQueries} from "./invalidateOrderQueries";

export const useCreateOrder = () => {
    const queryClient = useQueryClient();
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);
    const {createOrderUseCase} = container.orderContainer;

    return useMutation({
        mutationFn: async (variables: {input: OrderFormInput; idempotencyKey: string}) =>
            createOrderUseCase.execute(
                OrderFormMapper.toDomain(variables.input),
                variables.idempotencyKey,
            ),
        onMutate: () => ({userId, businessId}),
        onSuccess: async (_data, _variables, scope) => {
            await invalidateOrderQueries(queryClient, scope, undefined, "create");
        },
        onError: (error) => {
            console.error("CREATE ORDER FAILED:", error);
        },
    });
};
