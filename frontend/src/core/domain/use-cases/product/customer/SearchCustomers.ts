// core/application/use-cases/customer/SearchCustomers.ts

import type { CustomerRepository } from "../../../repositories/product/CustomerRepository";
import type {Customer} from "../../../entities/product/customer/Customer.ts";


export class SearchCustomers {
    constructor(
        private customerRepository: CustomerRepository,
    ) {}

    async execute(
        query: string,
    ): Promise<Customer[]> {

        const keyword = query.trim();

        if (!keyword) {
            return [];
        }

        return this.customerRepository.search(
            keyword,
        );

    }
}