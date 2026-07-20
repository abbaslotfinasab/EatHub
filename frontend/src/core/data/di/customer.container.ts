// data/di/customer.container.ts

import {CreateCustomer} from "../../domain/use-cases/product/customer/CreateCustomer";
import {FindAllCustomers} from "../../domain/use-cases/product/customer/FindAllCustomers";
import {SearchCustomers} from "../../domain/use-cases/product/customer/SearchCustomers";
import {CustomerRemoteDataSource} from "../datasources/CustomerRemoteDataSource";
import {CustomerRepositoryImpl} from "../repositories/CustomerRepositoryImpl";
import {UpdateCustomerBalance} from "../../domain/use-cases/product/customer/UpdateCustomerBalance.ts";

export const createCustomerContainer = () => {

    const remote =
        new CustomerRemoteDataSource();

    const repository =
        new CustomerRepositoryImpl(
            remote,
        );

    return {

        createCustomerUseCase:
            new CreateCustomer(
                repository,
            ),

        findAllCustomersUseCase:
            new FindAllCustomers(
                repository,
            ),

        searchCustomersUseCase:
            new SearchCustomers(
                repository,
            ),

        updateCustomerBalanceUseCase:
        new  UpdateCustomerBalance(
            repository,
            ),

        // updateCustomerUseCase:
        //     new UpdateCustomer(
        //         repository,
        //     ),

        // deleteCustomerUseCase:
        //     new DeleteCustomer(
        //         repository,
        //     ),

        // getCustomerByIdUseCase:
        //     new GetCustomerById(
        //         repository,
        //     ),

    };

};