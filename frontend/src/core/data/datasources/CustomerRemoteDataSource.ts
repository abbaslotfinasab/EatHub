// data/datasources/remote/customer/CustomerRemoteDataSource.ts

import type {CustomerDTO} from "../dtos/customer/CustomerDTO";
import {apiClient} from "../http/http-client";
import type {CreateCustomerDTO} from "../dtos/customer/CreateCustomerDTO.ts";
import type {UpdateCustomerDTO} from "../dtos/customer/UpdateCustomerDTO.ts";
import type {CustomerDetailDTO} from "../dtos/customer/CustomerDetailDTO.ts";


export class CustomerRemoteDataSource {

    // =========================
    // Create
    // =========================

    async create(
        input: CreateCustomerDTO,
    ): Promise<CustomerDTO> {

        const {data} =
            await apiClient.post<CustomerDTO>(
                "/products/customers/create",
                input,
            );

        return data;

    }

    // =========================
    // Update
    // =========================

    async update(
        payload: UpdateCustomerDTO,
    ): Promise<void> {

        await apiClient.put<CustomerDTO>(
            `/products/customers/${payload.id}/update/`,
            payload,
        );


    }

    // =========================
    // Delete
    // =========================

    async delete(
        id: string,
    ): Promise<void> {

        await apiClient.delete(
            `/products/customers/${id}/delete/`,
        );

    }

    // =========================
    // Detail
    // =========================

    async findById(
        id: string,
    ): Promise<CustomerDetailDTO> {

        const {data} =
            await apiClient.get<CustomerDetailDTO>(
                `/products/customers/${id}/`,
            );

        return data;

    }

    // =========================
    // List
    // =========================

    async findAll(): Promise<CustomerDTO[]> {

        const {data} =
            await apiClient.get<CustomerDTO[]>(
                "/products/customers/",
            );

        return data;

    }

    // =========================
    // Search
    // =========================

    async search(
        query: string,
    ): Promise<CustomerDTO[]> {

        const {data} =
            await apiClient.get<CustomerDTO[]>(
                "/products/customers/",
                {
                    params: {
                        search: query,
                    },
                },
            );

        return data;

    }

}