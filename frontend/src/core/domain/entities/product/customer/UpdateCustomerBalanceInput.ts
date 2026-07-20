import type {CustomerBalanceOperation} from "../../../objects/CustomerBalanceOperation.ts";

export interface UpdateCustomerBalanceInput {

    customerId: number;

    type: CustomerBalanceOperation;

    amount: number;

    description?: string;

}