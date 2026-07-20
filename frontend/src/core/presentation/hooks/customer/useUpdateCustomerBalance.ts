// presentation/hooks/customer/useUpdateCustomerBalance.ts

import {
    useMutation,
    useQueryClient,
} from "@tanstack/react-query";

import {container} from "../../../data/di/container";

import type {UpdateCustomerBalanceInput} from "../../../domain/entities/product/customer/UpdateCustomerBalanceInput";


export const useUpdateCustomerBalance = () => {

    const queryClient = useQueryClient();


    const {
        updateCustomerBalanceUseCase,
    } = container.customerContainer;


    return useMutation({

        mutationFn: async (
            input: UpdateCustomerBalanceInput,
        ) => {

            return updateCustomerBalanceUseCase.execute(
                input,
            );

        },


        onSuccess: (
            _,
            variables,
        ) => {

            queryClient.invalidateQueries({
                queryKey: [
                    "customers",
                ],
            });


            queryClient.invalidateQueries({
                queryKey: [
                    "customer",
                    variables.customerId,
                ],
            });


            queryClient.invalidateQueries({
                queryKey: [
                    "customer-transactions",
                    variables.customerId,
                ],
            });

        },


        onError: (error) => {

            console.error(
                "UPDATE CUSTOMER BALANCE FAILED:",
                error,
            );

        },

    });

};