// data/mappers/customer/customerAccountMapper.ts

import type { CustomerAccountDTO } from "../dtos/customer/CustomerAccountDTO";
import type {CustomerAccount} from "../../domain/entities/product/customer/CustomerAccount.ts";


export const customerAccountMapper = {

    toDomain(
        dto: CustomerAccountDTO,
    ): CustomerAccount {

        return {

            id: dto.id.toString(),

            customerId: dto.customer.id,

            balance: dto.balance,

            createdAt: dto.createdAt,

            updatedAt: dto.updatedAt,

        };

    },

};