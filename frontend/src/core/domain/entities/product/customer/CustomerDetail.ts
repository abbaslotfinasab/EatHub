// domain/entities/customer/CustomerWithTransactions.ts

import type { Customer } from "./Customer";
import type { CustomerAccount } from "./CustomerAccount";
import type { CustomerTransaction } from "./CustomerTransaction";

export interface CustomerDetail {
    customer: Customer;

    account: CustomerAccount;

    transactions: CustomerTransaction[];
}