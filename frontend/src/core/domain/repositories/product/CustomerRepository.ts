// domain/repositories/customer/CustomerRepository.ts


import type {Customer} from "../../entities/product/customer/Customer.ts";
import type {CustomerSearchFilters} from "../../objects/filters/CustomerSearchFilters.ts";
import type {CustomerDetail} from "../../entities/product/customer/CustomerDetail.ts";
import type {CustomerListItem} from "../../entities/product/customer/CustomerListItem.ts";
import type { UpdateCustomerBalanceInput } from "../../entities/product/customer/UpdateCustomerBalanceInput.ts";


export interface CustomerRepository {

    // =========================
    // Customer
    // =========================

    create(
        customer: Customer,
    ): Promise<Customer>;

    update(
        customer: Customer,
    ): Promise<void>;

    delete(
        id: string,
    ): Promise<void>;

    findById(
        id: string,
    ): Promise<CustomerDetail>;

    getAll(
        filters?: CustomerSearchFilters,
    ): Promise<CustomerListItem[]>;

    search(
        query: string,
    ): Promise<Customer[]>;

    updateBalance(
        input: UpdateCustomerBalanceInput,
    ): Promise<void>;

}