// presentation/hooks/customer/useSearchCustomers.ts

import { useQuery } from "@tanstack/react-query";

import { container } from "../../../data/di/container";

export const useSearchCustomers = (
    query: string,
) => {

    const {
        searchCustomersUseCase,
    } = container.customerContainer;

    return useQuery({

        queryKey: [
            "customers",
            "search",
            query,
        ],

        queryFn: () =>
            searchCustomersUseCase.execute(
                query,
            ),

        enabled:
            query.trim().length >= 2,

        staleTime:
            1000 * 60 * 5,

        gcTime:
            1000 * 60 * 10,

    });

};