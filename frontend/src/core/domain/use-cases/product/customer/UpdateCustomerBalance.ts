// domain/use-cases/product/customer/UpdateCustomerBalance.ts

import type {UpdateCustomerBalanceInput} from "../../../entities/product/customer/UpdateCustomerBalanceInput";
import { CustomerBalanceOperation } from "../../../objects/CustomerBalanceOperation.ts";
import type {CustomerRepository} from "../../../repositories/product/CustomerRepository.ts";

export class UpdateCustomerBalance {

    constructor(
        private readonly repository: CustomerRepository,
    ) {
    }

    async execute(
        input: UpdateCustomerBalanceInput,
    ): Promise<void> {


        if (
            input.type !== CustomerBalanceOperation.ADJUST
            &&
            input.amount <= 0
        ) {

            throw new Error(
                "Amount must be greater than zero.",
            );

        }

        return this.repository.updateBalance(
            input,
        );

    }

}