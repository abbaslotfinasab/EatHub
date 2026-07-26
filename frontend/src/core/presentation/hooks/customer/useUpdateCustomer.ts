import {useMutation, useQueryClient} from "@tanstack/react-query";

import {container} from "../../../data/di/container";

import type {Customer} from "../../../domain/entities/product/customer/Customer";

export const useUpdateCustomer = () => {

    const queryClient =
        useQueryClient();

    const {
        updateCustomerUseCase,
    } = container.customerContainer;

    return useMutation({

        mutationFn: (
            customer: Customer,
        ) =>
            updateCustomerUseCase.execute(
                customer,
            ),

        onSuccess: async () => {

            await queryClient.invalidateQueries({

                queryKey: ["customers"],

            });

        },

    });

};