import type {UpdateCustomerBalanceInput} from "../../domain/entities/product/customer/UpdateCustomerBalanceInput";
import type {CustomerBalanceDTO} from "../dtos/customer/CustomerBalanceDTO.ts";


export const customerBalanceMapper = {

    toDTO(
        input: UpdateCustomerBalanceInput,
    ): CustomerBalanceDTO {

        return {
            amount: input.amount,

            description:
                input.description,
        };

    },

};