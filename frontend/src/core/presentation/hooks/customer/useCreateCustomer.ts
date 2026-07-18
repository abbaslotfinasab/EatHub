// presentation/hooks/customer/useCreateCustomer.ts

import {
    useMutation,
    useQueryClient,
} from "@tanstack/react-query";

import { container } from "../../../data/di/container";

import type { CustomerFormInput } from "../../forms/customer/CustomerFormInput";
import { CustomerFormMapper } from "../../forms/customer/CustomerFormMapper";

export const useCreateCustomer = () => {

    const queryClient = useQueryClient();

    const {
        createCustomerUseCase,
    } = container.customerContainer;

    return useMutation({

        mutationFn: async (
            input: CustomerFormInput,
        ) => {

            const customer =
                CustomerFormMapper.toDomain(
                    input,
                );

            return createCustomerUseCase.execute(
                customer,
            );

        },

        onSuccess: () => {

            queryClient.invalidateQueries({
                queryKey: ["customers"],
            });

        },

        onError: (error) => {

            console.error(
                "CREATE CUSTOMER FAILED:",
                error,
            );

        },

    });

};