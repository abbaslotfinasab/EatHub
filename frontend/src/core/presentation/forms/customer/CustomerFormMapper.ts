// presentation/forms/customer/CustomerFormMapper.ts

import type { Customer } from "../../../domain/entities/product/customer/Customer";

import type { CustomerFormInput } from "./CustomerFormInput";

export class CustomerFormMapper {

    static toDomain(
        input: CustomerFormInput,
    ): Customer {

        return {

            name: input.name,

            phone: input.phone,

        };

    }

    static toFormInput(
        customer: Customer,
    ): CustomerFormInput {

        return {

            name: customer.name,

            phone: customer.phone,

        };

    }

}