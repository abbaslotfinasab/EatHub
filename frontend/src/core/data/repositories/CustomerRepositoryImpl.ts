// data/repositories/customer/CustomerRepositoryImpl.ts


import type {CustomerRepository} from "../../domain/repositories/product/CustomerRepository.ts";
import type {Customer} from "../../domain/entities/product/customer/Customer.ts";
import type {CustomerDetail} from "../../domain/entities/product/customer/CustomerDetail.ts";
import type {CustomerListItem} from "../../domain/entities/product/customer/CustomerListItem.ts";
import {customerMapper} from "../mappers/customerMapper.ts";
import type {CustomerRemoteDataSource} from "../datasources/CustomerRemoteDataSource.ts";
import {customerDetailMapper} from "../mappers/customerDetailMapper.ts";
import type {UpdateCustomerBalanceInput} from "../../domain/entities/product/customer/UpdateCustomerBalanceInput.ts";
import {customerBalanceMapper} from "../mappers/customerBalanceMapper.ts";

export class CustomerRepositoryImpl
    implements CustomerRepository {

    constructor(
        private remote: CustomerRemoteDataSource,
    ) {
    }

    // =========================
    // Create
    // =========================

    async create(
        customer: Customer,
    ): Promise<Customer> {

        const dto =
            await this.remote.create(
                customerMapper.toCreateDTO(customer),
            );

        return customerMapper.toDomain(dto);

    }

    // =========================
    // Update
    // =========================

    async update(
        customer: Customer,
    ): Promise<void> {

        const dto =
            customerMapper.toUpdateDTO(customer);

        await this.remote.update(dto);


    }

    // =========================
    // Delete
    // =========================

    async delete(
        id: string,
    ): Promise<void> {

        await this.remote.delete(id);

    }

    // =========================
    // Get By Id
    // =========================

    async findById(
        id: string,
    ): Promise<CustomerDetail> {

        const dto =
            await this.remote.findById(id);

        return customerDetailMapper.toDomain(
            dto,
        );

    }

    // =========================
    // Get All
    // =========================

    async findAll(): Promise<CustomerListItem[]> {

        const dtos =
            await this.remote.findAll();

        return customerMapper.toDomainList(
            dtos,
        );

    }

    // =========================
    // Search
    // =========================

    async search(
        query: string,
    ): Promise<Customer[]> {

        const dtos =
            await this.remote.search(
                query,
            );

        return dtos.map(
            customerMapper.toDomain,
        );

    }


    // =========================
// Balance
// =========================

   async updateBalance(
    input: UpdateCustomerBalanceInput,
): Promise<void> {

    await this.remote.updateBalance(
        customerBalanceMapper.toDTO(input),
        input.type,
        input.customerId,
    );

}

}