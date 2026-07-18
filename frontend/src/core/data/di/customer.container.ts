// data/di/customer.container.ts

import { CreateCustomer } from "../../domain/use-cases/product/customer/CreateCustomer";
import { SearchCustomers } from "../../domain/use-cases/product/customer/SearchCustomers";
import { CustomerRemoteDataSource } from "../datasources/CustomerRemoteDataSource";
import { CustomerRepositoryImpl } from "../repositories/CustomerRepositoryImpl";



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

        // updateCustomerUseCase:
        //     new UpdateCustomer(
        //         repository,
        //     ),

        // deleteCustomerUseCase:
        //     new DeleteCustomer(
        //         repository,
        //     ),
        //
        // getCustomerByIdUseCase:
        //     new GetCustomerById(
        //         repository,
        //     ),

        // getAllCustomersUseCase:
        //     new GetAllCustomers(
        //         repository,
        //     ),

        searchCustomersUseCase:
            new SearchCustomers(
                repository,
            ),

    };

};