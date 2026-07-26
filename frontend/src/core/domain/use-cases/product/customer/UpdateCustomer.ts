import type {Customer} from "../../../entities/product/customer/Customer";
import type {CustomerRepository} from "../../../repositories/product/CustomerRepository";

export class UpdateCustomer {

    constructor(
        private readonly repository: CustomerRepository,
    ) {}

    execute(
        customer: Customer,
    ): Promise<void> {

        return this.repository.update(
            customer,
        );

    }

}