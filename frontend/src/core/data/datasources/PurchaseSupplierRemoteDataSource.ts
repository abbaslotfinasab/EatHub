import { apiClient } from '../http/http-client.ts';
import type { PurchaseSupplierDTO, PurchaseSupplierWriteDTO } from '../dtos/purchase/PurchaseSupplierDTO.ts';

export class PurchaseSupplierRemoteDataSource {
    async list(filters?: { search?: string; isActive?: boolean }): Promise<PurchaseSupplierDTO[]> {
        const { data } = await apiClient.get<PurchaseSupplierDTO[]>('/purchase/suppliers/', {
            params: {
                ...(filters?.search ? { search: filters.search } : {}),
                ...(filters?.isActive === undefined ? {} : { is_active: filters.isActive }),
            },
        });
        return data;
    }

    async create(input: PurchaseSupplierWriteDTO): Promise<PurchaseSupplierDTO> {
        const { data } = await apiClient.post<PurchaseSupplierDTO>('/purchase/suppliers/', input);
        return data;
    }

    async update(id: string, input: PurchaseSupplierWriteDTO): Promise<PurchaseSupplierDTO> {
        const { data } = await apiClient.put<PurchaseSupplierDTO>(`/purchase/suppliers/${id}/`, input);
        return data;
    }
}
