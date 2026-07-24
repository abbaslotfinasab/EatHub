import {apiClient} from "../http/http-client";

import type {OrderDTO} from "../dtos/order/OrderDTO";
import type {CreateOrderDTO} from "../dtos/order/CreateOrderDTO";
import type {UpdateOrderDTO} from "../dtos/order/UpdateOrderDTO";
import type {UpdateOrderStatusDTO} from "../dtos/order/UpdateOrderStatusDTO.ts";
import type {OrderFilters} from "../../domain/objects/filters/OrderFilters.ts";

export class OrderRemoteDataSource {

    // =========================
    // Create
    // =========================

    async createOrder(payload: CreateOrderDTO): Promise<OrderDTO> {
        const {data} = await apiClient.post<OrderDTO>(
            "/products/orders/",
            payload,
        );

        return data;
    }

    // =========================
    // Read
    // =========================

    async getOrders(filters?: OrderFilters): Promise<OrderDTO[]> {
        const {data} = await apiClient.get<OrderDTO[]>(
            "/products/orders/list",
            {
                    params: filters,
                },
        );

        return data;
    }

    async getOrderById(id: string): Promise<OrderDTO> {
        const {data} = await apiClient.get<OrderDTO>(
            `/products/orders/${id}/`,
        );

        return data;
    }

    // =========================
    // Update
    // =========================

    async updateOrder(
        id: string,
        payload: UpdateOrderDTO,
    ): Promise<OrderDTO> {
        const {data} = await apiClient.patch<OrderDTO>(
            `/products/orders/${id}/update/`,
            payload,
        );

        return data;
    }

    async updateOrderStatus(
        id: string,
        status: string,
    ): Promise<OrderDTO> {
        const {data} = await apiClient.patch<OrderDTO>(
            `/products/orders/${id}/status/`,
            {status},
        );

        return data;
    }

    // =========================
    // Delete / Cancel
    // =========================

    async cancelOrder(id: string): Promise<OrderDTO> {
        const {data} = await apiClient.patch<OrderDTO>(
            `/products/orders/${id}/cancel/`,
        );

        return data;
    }

    async deleteOrder(id: string): Promise<void> {
        await apiClient.delete(
            `/products/orders/${id}/delete/`,
        );
    }

    // =========================
    // Filters / Lists
    // =========================

    async getActiveOrders(): Promise<OrderDTO[]> {
        const {data} = await apiClient.get<OrderDTO[]>(
            "/products/orders/active/",
        );

        return data;
    }

    async getOrderHistory(): Promise<OrderDTO[]> {
        const {data} = await apiClient.get<OrderDTO[]>(
            "/products/orders/history/",
        );

        return data;
    }

    async updateStatus(
        orderId: string,
        input: UpdateOrderStatusDTO,
    ): Promise<void> {


        await apiClient.patch(
            `/products/orders/${orderId}/status/`,
            input,
        );

    }


}