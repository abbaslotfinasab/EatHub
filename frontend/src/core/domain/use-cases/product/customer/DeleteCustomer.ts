import type {CustomerRepository} from "../../../repositories/product/CustomerRepository";

export class DeleteCustomer {

    constructor(
        private readonly repository: CustomerRepository,
    ) {}

    execute(
        id: string,
    ): Promise<void> {

        return this.repository.delete(
            id,
        );

    }

}