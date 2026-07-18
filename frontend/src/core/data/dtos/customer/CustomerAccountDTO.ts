import type {CustomerDTO} from "./CustomerDTO.ts";

export interface CustomerAccountDTO {
    id: string;

    customer: CustomerDTO;

    balance: number;

    createdAt?: string;

    updatedAt?: string;
}