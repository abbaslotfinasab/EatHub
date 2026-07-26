// presentation/hooks/customer/useGetCustomerById.ts

import { useQuery } from "@tanstack/react-query";

import { container } from "../../../data/di/container";

export const useGetCustomerById = (
    id?: string
) => {

    const {
        getCustomerByIdUseCase,
    } = container.customerContainer;

    return useQuery({

        queryKey: [
            "customer",
            id,
        ],

        queryFn: () =>
            getCustomerByIdUseCase.execute(
                id!,
            ),

        enabled: Boolean(id),

    });

};