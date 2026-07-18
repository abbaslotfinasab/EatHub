import type {CustomerDTO} from "./CustomerDTO.ts";

export interface CustomerAccountDTO {
    id: number;

    customer: CustomerDTO;

    balance: number;

    createdAt?: string;

    updatedAt?: string;
}