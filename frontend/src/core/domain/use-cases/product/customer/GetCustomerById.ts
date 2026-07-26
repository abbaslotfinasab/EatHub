// domain/use-cases/product/customer/GetCustomerById.ts

import type { CustomerDetail } from "../../../entities/product/customer/CustomerDetail";
import type { CustomerRepository } from "../../../repositories/product/CustomerRepository";

export class GetCustomerById {

    constructor(
        private readonly repository: CustomerRepository,
    ) {}

    execute(
        id: string,
    ): Promise<CustomerDetail> {

        return this.repository.findById(
            id,
        );

    }

}