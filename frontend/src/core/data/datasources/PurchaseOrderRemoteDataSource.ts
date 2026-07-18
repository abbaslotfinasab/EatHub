import { apiClient } from "../http/http-client";

import type { PurchaseOrderStatusType } from "../../domain/entities/inventory/facture/PurchaseOrder";

import type { PurchaseOrderFilters } from "../../domain/objects/filters/PurchaseOrderFilters";
import type { CreatePurchaseOrderDTO } from "../dtos/facture/CreatePurchaseOrderDTO";
import type { PurchaseOrderDTO } from "../dtos/facture/PurchaseOrderDTO";
import type {UpdatePurchaseOrderDTO} from "../dtos/facture/UpdatePurchaseOrderDTO.ts";

export class PurchaseOrderRemoteDataSource {

    // =========================
    // CREATE
    // =========================

    async createPurchaseOrder(
        payload: CreatePurchaseOrderDTO,
    ): Promise<PurchaseOrderDTO> {
        const { data } = await apiClient.post<PurchaseOrderDTO>(
            "/inventory/purchase-orders/create/",
            payload,
        );

        return data;
    }

    // =========================
    // READ
    // =========================

    async getPurchaseOrders(
        filters?: PurchaseOrderFilters,
    ): Promise<PurchaseOrderDTO[]> {
        const { data } = await apiClient.get<PurchaseOrderDTO[]>(
            "/inventory/purchase-orders/",
            {
                params: filters,
            },
        );

        return data;
    }

    async getPurchaseOrderById(
        id: string,
    ): Promise<PurchaseOrderDTO> {
        const { data } = await apiClient.get<PurchaseOrderDTO>(
            `/inventory/purchase-orders/${id}/`,
        );

        return data;
    }

    // =========================
    // UPDATE
    // =========================

    async updatePurchaseOrder(
        id: string,
        payload: UpdatePurchaseOrderDTO,
    ): Promise<PurchaseOrderDTO> {
        const { data } = await apiClient.patch<PurchaseOrderDTO>(
            `/inventory/purchase-orders/${id}/update/`,
            payload,
        );

        return data;
    }

    async updatePurchaseOrderStatus(
        id: string,
        status: PurchaseOrderStatusType,
    ): Promise<PurchaseOrderDTO> {
        const { data } = await apiClient.patch<PurchaseOrderDTO>(
            `/inventory/purchase-orders/${id}/status/`,
            { status },
        );

        return data;
    }

    // =========================
    // DELETE
    // =========================

    async deletePurchaseOrder(
        id: string,
    ): Promise<void> {
        await apiClient.delete(
            `/inventory/purchase-orders/${id}/delete/`,
        );
    }

}