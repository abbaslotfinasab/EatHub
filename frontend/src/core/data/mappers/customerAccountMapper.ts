// data/mappers/customer/customerAccountMapper.ts

import type { CustomerAccountDTO } from "../dtos/customer/CustomerAccountDTO";
import type { CustomerAccount } from "../../domain/entities/product/customer/CustomerAccount";

export const customerAccountMapper = {

    toDomain(
        dto: CustomerAccountDTO | null,
    ): CustomerAccount | null {

        if (!dto) {
            return null;
        }

        return {

            id: dto.id.toString(),

            customerId: dto.customer.id,

            balance: dto.balance,

            createdAt: dto.createdAt,

            updatedAt: dto.updatedAt,

        };

    },

};