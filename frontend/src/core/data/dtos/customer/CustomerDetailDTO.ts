import type { CustomerDTO } from "./CustomerDTO";
import type {CustomerAccountDTO} from "./CustomerAccountDTO.ts";
import type {CustomerTransactionDTO} from "./CustomerTransactionDTO.ts";

export interface CustomerDetailDTO {

    customer: CustomerDTO;

    account: CustomerAccountDTO;

    transactions: CustomerTransactionDTO[];

}