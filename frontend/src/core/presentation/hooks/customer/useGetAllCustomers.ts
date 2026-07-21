// presentation/hooks/customer/useCustomers.ts

import {useQuery} from "@tanstack/react-query";

import {container} from "../../../data/di/container";
import type {CustomerSearchFilters} from "../../../domain/objects/filters/CustomerSearchFilters.ts";

export const useGetAllCustomers = (
    filters?: CustomerSearchFilters,
) => {

    const {
        findAllCustomersUseCase,
    } = container.customerContainer;

    return useQuery({
        queryKey: [
            "customers",
            filters,
        ],
        queryFn: () =>
            findAllCustomersUseCase.execute(filters),

        placeholderData: (previousData) => previousData,
    });

};