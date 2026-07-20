import {OrderRemoteDataSource} from "../datasources/OrderRemoteDataSource";
import {OrderRepositoryImpl} from "../repositories/OrderRepositoryImpl";

import {CreateOrder} from "../../domain/use-cases/product/order/CreateOrder";
import {UpdateOrder} from "../../domain/use-cases/product/order/UpdateOrder";
import {DeleteOrder} from "../../domain/use-cases/product/order/DeleteOrder";
import {GetAllOrdersWithItems} from "../../domain/use-cases/product/order/GetAllOrdersWithItems.ts";
import {GetOrderByIdWithItems} from "../../domain/use-cases/product/order/GetOrderByIdWithItems.ts";
import {UpdateOrderStatus} from "../../domain/use-cases/product/order/UpdateOrderStatus.ts";

export const createOrderContainer = () => {
    const remote = new OrderRemoteDataSource();

    const repository = new OrderRepositoryImpl(remote);

    return {
        createOrderUseCase: new CreateOrder(repository),

        getAllOrdersUseCase: new GetAllOrdersWithItems(repository),

        getOrderByIdUseCase: new GetOrderByIdWithItems(repository),

        updateOrderUseCase: new UpdateOrder(repository),

        deleteOrderUseCase: new DeleteOrder(repository),

        updateOrderStatusUseCase:
            new UpdateOrderStatus(
                repository,
            ),
    };
};