import type {OrderRepository} from "../../domain/repositories/product/OrderRepository.ts";
import type {OrderWithItems} from "../../domain/entities/product/order/OrderWithItems.ts";


import {OrderRemoteDataSource} from "../datasources/OrderRemoteDataSource";
import {orderMapper} from "../mappers/orderMapper";
import type {UpdateOrderStatusInput} from "../../domain/entities/product/order/UpdateOrderStatusInput.ts";
import type {UpdateOrderStatusDTO} from "../dtos/order/UpdateOrderStatusDTO.ts";

export class OrderRepositoryImpl implements OrderRepository {

    constructor(
        private remote: OrderRemoteDataSource,
    ) {
    }

    // =========================
    // CREATE
    // =========================

    async create(input: OrderWithItems): Promise<void> {
        const dto = orderMapper.toCreateDTO(input);

        await this.remote.createOrder(dto);
    }

    // =========================
    // READ
    // =========================

    async findAll(): Promise<OrderWithItems[]> {
        const data = await this.remote.getOrders();

        return data.map(orderMapper.toDomain);
    }

    async findById(id: string): Promise<OrderWithItems | null> {
        const data = await this.remote.getOrderById(id);

        if (!data) return null;

        return orderMapper.toDomain(data);
    }

    // =========================
    // UPDATE
    // =========================

    async update(id: string, order: OrderWithItems): Promise<void> {
        if (!id) {
            throw new Error("Order id is required");
        }

        const dto = orderMapper.toUpdateDTO(order);

        await this.remote.updateOrder(
            id,
            dto,
        );
    }

    // =========================
    // DELETE
    // =========================

    async delete(id: string): Promise<void> {
        await this.remote.deleteOrder(id);
    }

    async updateStatus(
        input: UpdateOrderStatusInput,
    ): Promise<void> {


        const dto: UpdateOrderStatusDTO = {

            status: input.status,

            payment_status:
            input.paymentStatus,

            payment_method:
            input.paymentMethod,

        };


        await this.remote.updateStatus(
            input.orderId,
            dto,
        );
    }
}
