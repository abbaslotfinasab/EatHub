// core/domain/use-cases/customer/FindAllCustomersUseCase.ts

import type { CustomerSearchFilters } from "../../../objects/filters/CustomerSearchFilters";
import type { CustomerRepository } from "../../../repositories/product/CustomerRepository";
import type {CustomerListItem} from "../../../entities/product/customer/CustomerListItem.ts";


export class GetAllCustomers {

    constructor(
        private readonly customerRepository: CustomerRepository,
    ) {}

    execute(
        filters?: CustomerSearchFilters,
    ): Promise<CustomerListItem[]> {

        return this.customerRepository.getAll(
            filters,
        );

    }

}