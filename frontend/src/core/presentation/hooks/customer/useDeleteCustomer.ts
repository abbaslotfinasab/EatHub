import {useMutation, useQueryClient} from "@tanstack/react-query";

import {container} from "../../../data/di/container";

export const useDeleteCustomer = () => {

    const queryClient =
        useQueryClient();

    const {
        deleteCustomerUseCase,
    } = container.customerContainer;

    return useMutation({

        mutationFn: (
            id: string,
        ) =>
            deleteCustomerUseCase.execute(
                id,
            ),

        onSuccess: async () => {

            await queryClient.invalidateQueries({

                queryKey: ["customers"],

            });

        },

    });

};