import type { AccountsPayable, AccountsPayableFilters } from '../../entities/inventory/AccountsPayable.ts';

export interface AccountsPayableRepository {
    list(filters?: AccountsPayableFilters): Promise<AccountsPayable[]>;
}
