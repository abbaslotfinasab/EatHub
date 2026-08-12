import type {CustomerAccountDTO} from "./CustomerAccountDTO.ts";
import type {OrderDTO} from "../order/OrderDTO.ts";

export interface CustomerTransactionDTO {
    id: string;

    account: CustomerAccountDTO;

    order: OrderDTO;

    type: string;

    amount: number;

    balance_after : number;

    description?: string | null;

    created_at?: string;
}