// core/data/repositories/PurchaseOrderRepositoryImpl.ts
import { apiClient } from '../api/http-client';
import { isAxiosError } from 'axios';
import type {
    PurchaseOrderFilters,
    PurchaseOrderRepository
} from "../../domain/repositories/inventory/PurchaseOrderRepository.ts";
import type {PurchaseOrder, PurchaseOrderStatusType} from "../../domain/entities/inventory/PurchaseOrder.ts";

export class PurchaseOrderRepositoryImpl implements PurchaseOrderRepository {
    async createWithItems(data: {
        supplierId: string;
        expectedDeliveryDate?: string | null;
        invoiceNumber?: string | null;
        notes?: string | null;
        items: Array<{
            ingredientId: string;
            quantity: number;
            unitPrice: number;
        }>;
    }): Promise<PurchaseOrder> {
        const response = await apiClient.post('/purchase-orders/with-items', data);
        return response.data;
    }

    async findById(id: string): Promise<PurchaseOrder | null> {
        try {
            const response = await apiClient.get(`/purchase-orders/${id}`);
            return response.data;
        } catch (error) {
            if (isAxiosError(error) && error.response?.status === 404) {
                return null;
            }
            throw error;
        }
    }

    async findAll(filters?: PurchaseOrderFilters): Promise<PurchaseOrder[]> {
        const params = new URLSearchParams();
        if (filters) {
            Object.entries(filters).forEach(([key, value]) => {
                if (value !== undefined && value !== null) {
                    params.append(key, String(value));
                }
            });
        }
        const queryString = params.toString();
        const url = queryString ? `/purchase-orders?${queryString}` : '/purchase-orders';
        const response = await apiClient.get(url);
        return response.data;
    }

    async update(id: string, data: Partial<PurchaseOrder>): Promise<PurchaseOrder> {
        const response = await apiClient.patch(`/purchase-orders/${id}`, data);
        return response.data;
    }

    async updateStatus(id: string, status: PurchaseOrderStatusType): Promise<void> {
        await apiClient.patch(`/purchase-orders/${id}/status`, { status });
    }

    async delete(id: string): Promise<void> {
        await apiClient.delete(`/purchase-orders/${id}`);
    }

    async save(order: PurchaseOrder): Promise<void> {
        await apiClient.delete(`/purchase-orders/${order}`);
    }

    async updateWithItems(id: string, data: {
        supplierId?: string;
        expectedDeliveryDate?: string | null;
        invoiceNumber?: string | null;
        notes?: string | null;
        status?: PurchaseOrderStatusType;
        items?: Array<{ ingredientId: string; quantity: number; unitPrice: number }>
    }): Promise<void> {
        const response = await apiClient.patch(`/purchase-orders/${id}`, data);
        return response.data;
    }
}