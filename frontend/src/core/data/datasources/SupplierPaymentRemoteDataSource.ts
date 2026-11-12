import { apiClient } from '../http/http-client.ts';
import type { CreateSupplierPaymentDTO, SupplierPaymentDTO } from '../dtos/purchase/SupplierPaymentDTO.ts';
import type { SupplierPaymentFilters } from '../../domain/entities/inventory/SupplierPayment.ts';

export class SupplierPaymentRemoteDataSource {
    async list(filters?: SupplierPaymentFilters): Promise<SupplierPaymentDTO[]> {
        const { data } = await apiClient.get<SupplierPaymentDTO[]>('/purchase/supplier-payments/', {
            params: {
                ...(filters?.supplierId ? { supplier_id: Number(filters.supplierId) } : {}),
                ...(filters?.method ? { method: filters.method } : {}),
                ...(filters?.paymentDateFrom ? { payment_date_from: filters.paymentDateFrom } : {}),
                ...(filters?.paymentDateTo ? { payment_date_to: filters.paymentDateTo } : {}),
            },
        });
        return data;
    }

    async create(input: CreateSupplierPaymentDTO): Promise<SupplierPaymentDTO> {
        const { data } = await apiClient.post<SupplierPaymentDTO>('/purchase/supplier-payments/', input);
        return data;
    }
}
