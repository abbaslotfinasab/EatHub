// data/mappers/customer/customerTransactionMapper.ts


import type {CustomerTransactionDTO} from "../dtos/customer/CustomerTransactionDTO.ts";
import {CustomerTransactionType, type CustomerTransaction} from "../../domain/entities/product/customer/CustomerTransaction.ts";

export const customerTransactionMapper = {

    toDomain(
        dto: CustomerTransactionDTO,
    ): CustomerTransaction {

        return {

            id: dto.id,

            accountId: dto.account.id,

            orderId: dto.order?.id,

            type:
                dto.type === "credit"
                    ? CustomerTransactionType.CREDIT
                    : dto.type === "debit"
                        ? CustomerTransactionType.DEBIT
                        : CustomerTransactionType.ADJUST,
            amount: dto.amount,

            description: dto.description,

            createdAt: dto.createdAt,

        };

    },

};