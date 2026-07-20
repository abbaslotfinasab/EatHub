export type CustomerBalanceOperation =
    | "credit"
    | "debit"
    | "adjust";

export interface UpdateCustomerBalanceInput {

    customerId: number;

    type: CustomerBalanceOperation;

    amount: number;

    description?: string;

}