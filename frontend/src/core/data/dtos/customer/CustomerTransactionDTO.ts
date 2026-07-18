import type {CustomerAccountDTO} from "./CustomerAccountDTO.ts";
import type {OrderDTO} from "../order/OrderDTO.ts";

export interface CustomerTransactionDTO {
    id: string;

    account: CustomerAccountDTO;

    order: OrderDTO;

    type: string;

    amount: number;

    description?: string | null;

    createdAt?: string;
}