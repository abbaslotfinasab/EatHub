// data/mappers/customer/customerMapper.ts

import type {Customer} from "../../domain/entities/product/customer/Customer";
import type {CustomerListItem} from "../../domain/entities/product/customer/CustomerListItem";
import type {CustomerDTO} from "../dtos/customer/CustomerDTO";
import type {CreateCustomerDTO} from "../dtos/customer/CreateCustomerDTO.ts";
import type {UpdateCustomerDTO} from "../dtos/customer/UpdateCustomerDTO.ts";


export const customerMapper = {

    toDomain(dto: CustomerDTO): Customer {

        return {
            id: dto.id,

            name: dto.name,
            phone: dto.phone,

            userId: dto.user_id ?? null,

        };

    },

    toDomainList(
        dtos: CustomerDTO[],
    ): CustomerListItem[] {

        return dtos.map(dto => ({

            id: dto.id,

            name: dto.name,

            phone: dto.phone,

            totalOrders: dto.totalOrders,

            totalSpent: dto.totalSpent,

            balance: dto.balance,


        }));

    },

    toCreateDTO(
        customer: Customer,
    ): CreateCustomerDTO {

        return {

            name: customer.name,

            phone: customer.phone,

        };

    },

    toUpdateDTO(
        customer: Customer,
    ): UpdateCustomerDTO {

        return {

            id: customer.id!,

            name: customer.name,

            phone: customer.phone,

        };

    },

};