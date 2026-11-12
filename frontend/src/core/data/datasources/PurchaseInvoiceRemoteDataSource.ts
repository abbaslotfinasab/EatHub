import { apiClient } from '../http/http-client.ts';
import type {
    PostPurchaseInvoiceResponseDTO,
    PurchaseInvoiceDTO,
    PurchaseInvoiceMatchResponseDTO,
    PurchaseInvoiceWriteDTO,
    PurchaseInvoiceEventDTO,
} from '../dtos/purchase/PurchaseInvoiceDTO.ts';

export class PurchaseInvoiceRemoteDataSource {
    async list(filters?: { supplierId?: string; purchaseOrderId?: string; dateFrom?: string; dateTo?: string }): Promise<PurchaseInvoiceDTO[]> {
        const { data } = await apiClient.get<PurchaseInvoiceDTO[]>('/purchase/purchase-invoices/', {
            params: {
                ...(filters?.supplierId ? { supplier_id: Number(filters.supplierId) } : {}),
                ...(filters?.purchaseOrderId ? { purchase_order_id: Number(filters.purchaseOrderId) } : {}),
                ...(filters?.dateFrom ? { invoice_date_from: filters.dateFrom } : {}),
                ...(filters?.dateTo ? { invoice_date_to: filters.dateTo } : {}),
            },
        });
        return data;
    }

    async get(id: string): Promise<PurchaseInvoiceDTO> {
        const { data } = await apiClient.get<PurchaseInvoiceDTO>(`/purchase/purchase-invoices/${id}/`);
        return data;
    }

    async create(input: PurchaseInvoiceWriteDTO): Promise<PurchaseInvoiceDTO> {
        const { data } = await apiClient.post<PurchaseInvoiceDTO>('/purchase/purchase-invoices/', input);
        return data;
    }

    async update(id: string, input: PurchaseInvoiceWriteDTO): Promise<PurchaseInvoiceDTO> {
        const { data } = await apiClient.put<PurchaseInvoiceDTO>(`/purchase/purchase-invoices/${id}/`, input);
        return data;
    }

    async approve(id: string): Promise<PurchaseInvoiceDTO> {
        const { data } = await apiClient.post<PurchaseInvoiceDTO>(`/purchase/purchase-invoices/${id}/approve/`, {});
        return data;
    }

    async match(id: string, persist: boolean): Promise<PurchaseInvoiceMatchResponseDTO> {
        const url = `/purchase/purchase-invoices/${id}/match/`;
        const { data } = persist
            ? await apiClient.post<PurchaseInvoiceMatchResponseDTO>(url, {})
            : await apiClient.get<PurchaseInvoiceMatchResponseDTO>(url);
        return data;
    }

    async post(id: string, dueDate?: string): Promise<PostPurchaseInvoiceResponseDTO> {
        const { data } = await apiClient.post<PostPurchaseInvoiceResponseDTO>(
            `/purchase/purchase-invoices/${id}/post/`,
            dueDate ? { due_date: dueDate } : {},
        );
        return data;
    }


    async events(id: string): Promise<PurchaseInvoiceEventDTO[]> {
        const { data } = await apiClient.get<PurchaseInvoiceEventDTO[]>(`/purchase/purchase-invoices/${id}/events/`);
        return data;
    }

    async cancel(id: string, reason: string): Promise<PurchaseInvoiceDTO> {
        const { data } = await apiClient.post<PurchaseInvoiceDTO>(
            `/purchase/purchase-invoices/${id}/cancel/`,
            { reason },
        );
        return data;
    }
}
