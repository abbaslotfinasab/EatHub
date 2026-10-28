import { useQuery } from "@tanstack/react-query";
import {container} from "../../../data/di/container.ts";


import type {OrderFilters} from "../../../domain/objects/filters/OrderFilters";
import {useAuthStore} from "../../store/auth.store";
import {orderQueryKeys} from "./orderQueryKeys.ts";


export const useGetAllOrders = (
    filters?: OrderFilters
) => {

    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore((state) => state.me?.active_business?.id ?? null);

    const {
        getAllOrdersUseCase
    } = container.orderContainer;


    return useQuery({

        queryKey: orderQueryKeys.list(userId, businessId, filters),


        queryFn: () =>
            getAllOrdersUseCase.execute(
                filters
            ),

        enabled: businessId !== null,


        placeholderData: (previous, previousQuery) =>
            previousQuery?.queryKey[1] === userId
            && previousQuery.queryKey[2] === businessId
                ? previous
                : undefined,

    });

};
