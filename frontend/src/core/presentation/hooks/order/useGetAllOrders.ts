import { useQuery } from "@tanstack/react-query";
import {container} from "../../../data/di/container.ts";


import type {OrderFilters} from "../../../domain/objects/filters/OrderFilters";


export const useGetAllOrders = (
    filters?: OrderFilters
) => {

    const {
        getAllOrdersUseCase
    } = container.orderContainer;


    return useQuery({

        queryKey:[
            "orders",
            filters,
        ],


        queryFn: () =>
            getAllOrdersUseCase.execute(
                filters
            ),


        placeholderData:
            (previous) => previous,

    });

};