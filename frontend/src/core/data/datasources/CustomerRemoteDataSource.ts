// data/datasources/remote/customer/CustomerRemoteDataSource.ts

import type {CustomerDTO} from "../dtos/customer/CustomerDTO";
import {apiClient} from "../http/http-client";
import type {CreateCustomerDTO} from "../dtos/customer/CreateCustomerDTO.ts";
import type {UpdateCustomerDTO} from "../dtos/customer/UpdateCustomerDTO.ts";
import type {CustomerDetailDTO} from "../dtos/customer/CustomerDetailDTO.ts";
import type {CustomerBalanceDTO} from "../dtos/customer/CustomerBalanceDTO.ts";
import type {CustomerBalanceOperation} from "../../domain/objects/CustomerBalanceOperation.ts";


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


    // =========================
// Balance
// =========================
    async updateBalance(
        input: CustomerBalanceDTO,
        type: CustomerBalanceOperation,
        customerId: number,
    ): Promise<void> {

        const endpoint =
            (() => {

                switch (type) {

                    case "credit":
                        return `/products/customers/${customerId}/credit/`;

                    case "debit":
                        return `/products/customers/${customerId}/debit/`;

                    case "adjust":
                        return `/products/customers/${customerId}/adjust/`;

                    default:
                        throw new Error(
                            "Invalid customer balance operation",
                        );
                }

            })();


        await apiClient.post(
            endpoint,
            {
                amount: input.amount,
                 description: input.description || "",
            },
        );

    }

}