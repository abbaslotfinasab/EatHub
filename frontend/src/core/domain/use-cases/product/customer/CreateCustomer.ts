// domain/use-cases/customer/CreateCustomer.ts

import type { CustomerRepository } from "../../../repositories/product/CustomerRepository";
import type {Customer} from "../../../entities/product/customer/Customer.ts";


export class CreateCustomer {
    constructor(
        private customerRepository: CustomerRepository,
    ) {}

    async execute(
        customer: Customer,
    ): Promise<Customer> {
        return this.customerRepository.create(
            customer,
        );
    }
}