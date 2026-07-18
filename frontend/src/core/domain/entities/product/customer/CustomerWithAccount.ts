// domain/entities/customer/Customer.ts

import type {Customer} from "./Customer.ts";
import type {CustomerAccount} from "./CustomerAccount.ts";

export interface CustomerWithAccount {
    customer:Customer;
    account:CustomerAccount
}