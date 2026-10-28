import { apiClient } from '../http/http-client.ts';
import type {
    CreateGoodsReceiptDTO,
    GoodsReceiptReadDTO,
    PurchaseOrderReadDTO,
    SupplierSummaryDTO,
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
