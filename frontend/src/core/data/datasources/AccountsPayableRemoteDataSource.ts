import { apiClient } from '../http/http-client.ts';
import type { AccountsPayableDTO } from '../dtos/purchase/AccountsPayableDTO.ts';
import type { AccountsPayableFilters } from '../../domain/entities/inventory/AccountsPayable.ts';

export class AccountsPayableRemoteDataSource {
    async list(filters?: AccountsPayableFilters): Promise<AccountsPayableDTO[]> {
        const { data } = await apiClient.get<AccountsPayableDTO[]>('/purchase/accounts-payables/', {
            params: {
                ...(filters?.status ? { status: filters.status } : {}),
                ...(filters?.supplierId ? { supplier_id: Number(filters.supplierId) } : {}),
                ...(filters?.dueDateFrom ? { due_date_from: filters.dueDateFrom } : {}),
                ...(filters?.dueDateTo ? { due_date_to: filters.dueDateTo } : {}),
            },
        });
        return data;
    }
}
