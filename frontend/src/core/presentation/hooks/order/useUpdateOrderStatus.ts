import {
    useMutation,
    useQueryClient,
} from "@tanstack/react-query";

import {container} from "../../../data/di/container";

import type {UpdateOrderStatusInput} from "../../../domain/entities/product/order/UpdateOrderStatusInput";


export const useUpdateOrderStatus = () => {


    const queryClient = useQueryClient();


    const {
        updateOrderStatusUseCase,
    } = container.orderContainer;



    return useMutation({

        mutationFn: async (
            input: UpdateOrderStatusInput,
        ) => {

            return updateOrderStatusUseCase.execute(
                input,
            );

        },


        onSuccess: () => {


            queryClient.invalidateQueries({

                queryKey: [
                    "orders",
                ],

            });


        },


        onError: (error) => {

            console.error(
                "UPDATE ORDER STATUS FAILED:",
                error,
            );

        },

    });


};