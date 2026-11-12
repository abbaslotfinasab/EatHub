import type { AccountsPayableFilters } from '../../../entities/inventory/AccountsPayable.ts';
import type { AccountsPayableRepository } from '../../../repositories/inventory/AccountsPayableRepository.ts';

const validId = (value: string) => /^\d+$/.test(value) && Number(value) > 0;

export class ListAccountsPayables {
    constructor(private readonly repository: AccountsPayableRepository) {}

    execute(filters?: AccountsPayableFilters) {
        if (filters?.supplierId && !validId(filters.supplierId)) {
            throw new Error('شناسه تأمین‌کننده معتبر نیست.');
        }
        if (filters?.dueDateFrom && filters?.dueDateTo && filters.dueDateFrom > filters.dueDateTo) {
            throw new Error('بازه سررسید معتبر نیست.');
        }
        return this.repository.list(filters);
    }
}
