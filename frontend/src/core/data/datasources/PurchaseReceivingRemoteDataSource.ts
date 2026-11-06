import { apiClient } from '../http/http-client.ts';
import type {
    CreateGoodsReceiptDTO,
    CreatePurchaseOrderDTO,
    GoodsReceiptReadDTO,
    PurchaseOrderReadDTO,
    SupplierSummaryDTO,
    UpdatePurchaseOrderDTO,
} from '../dtos/purchase/PurchaseReceivingDTO.ts';

export class PurchaseReceivingRemoteDataSource {
    async listOrders(): Promise<PurchaseOrderReadDTO[]> {
        const { data } = await apiClient.get<PurchaseOrderReadDTO[]>('/purchase/purchase-orders/');
        return data;
    }

    async getOrder(id: string): Promise<PurchaseOrderReadDTO> {
        const { data } = await apiClient.get<PurchaseOrderReadDTO>(`/purchase/purchase-orders/${id}/`);
        return data;
    }

    async createOrder(payload: CreatePurchaseOrderDTO): Promise<PurchaseOrderReadDTO> {
        const { data } = await apiClient.post<PurchaseOrderReadDTO>('/purchase/purchase-orders/', payload);
        return data;
    }

    async updateOrder(id: string, payload: UpdatePurchaseOrderDTO): Promise<PurchaseOrderReadDTO> {
        const { data } = await apiClient.put<PurchaseOrderReadDTO>(`/purchase/purchase-orders/${id}/`, payload);
        return data;
    }

    async sendOrder(id: string): Promise<PurchaseOrderReadDTO> {
        const { data } = await apiClient.post<PurchaseOrderReadDTO>(`/purchase/purchase-orders/${id}/send/`);
        return data;
    }

    async cancelOrder(id: string): Promise<PurchaseOrderReadDTO> {
        const { data } = await apiClient.post<PurchaseOrderReadDTO>(`/purchase/purchase-orders/${id}/cancel/`);
        return data;
    }

    async listReceipts(orderId: string): Promise<GoodsReceiptReadDTO[]> {
        const { data } = await apiClient.get<GoodsReceiptReadDTO[]>('/purchase/goods-receipts/', {
            params: { purchase_order_id: orderId },
        });
        return data;
    }

    async createReceipt(payload: CreateGoodsReceiptDTO): Promise<GoodsReceiptReadDTO> {
        const { data } = await apiClient.post<GoodsReceiptReadDTO>('/purchase/goods-receipts/', payload);
        return data;
    }

    async listSuppliers(): Promise<SupplierSummaryDTO[]> {
        const { data } = await apiClient.get<SupplierSummaryDTO[]>('/purchase/suppliers/', {
            params: { is_active: true },
        });
        return data;
    }
}
