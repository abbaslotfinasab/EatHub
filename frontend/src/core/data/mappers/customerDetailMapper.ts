// data/mappers/customer/customerDetailMapper.ts



import { customerMapper } from "./customerMapper";
import { customerAccountMapper } from "./customerAccountMapper";
import { customerTransactionMapper } from "./customerTransactionMapper";
import type {CustomerDetailDTO} from "../dtos/customer/CustomerDetailDTO.ts";
import type {CustomerDetail} from "../../domain/entities/product/customer/CustomerDetail.ts";

export const customerDetailMapper = {

    toDomain(
        dto: CustomerDetailDTO,
    ): CustomerDetail {

        return {

            customer:
                customerMapper.toDomain(
                    dto.customer,
                ),

            account:
                customerAccountMapper.toDomain(
                    dto.account,
                ),

            transactions:
                dto.transactions.map(
                    customerTransactionMapper.toDomain,
                ),

        };

    },

};