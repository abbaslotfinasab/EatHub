import type { PurchaseOrderRepository } from "../../domain/repositories/inventory/PurchaseOrderRepository";

import type { PurchaseOrderWithItems } from "../../domain/entities/inventory/facture/PurchaseOrderWithItems";
import type { PurchaseOrderFilters } from "../../domain/objects/filters/PurchaseOrderFilters";
import type { PurchaseOrderStatusType } from "../../domain/entities/inventory/facture/PurchaseOrder";

import { PurchaseOrderRemoteDataSource } from "../datasources/PurchaseOrderRemoteDataSource";
import { purchaseOrderMapper } from "../mappers/factureMapper";

export class PurchaseOrderRepositoryImpl implements PurchaseOrderRepository {

    constructor(
        private remote: PurchaseOrderRemoteDataSource,
    ) {}

    // =========================
    // CREATE
    // =========================

    async create(input: PurchaseOrderWithItems): Promise<void> {
        const dto = purchaseOrderMapper.toCreateDTO(input);

        await this.remote.createPurchaseOrder(dto);
    }

    // =========================
    // READ
    // =========================

    async findAll(
        filters?: PurchaseOrderFilters,
    ): Promise<PurchaseOrderWithItems[]> {
        const data = await this.remote.getPurchaseOrders(filters);

        return data.map(purchaseOrderMapper.toDomain);
    }

    async findById(
        id: string,
    ): Promise<PurchaseOrderWithItems | null> {
        const data = await this.remote.getPurchaseOrderById(id);

        if (!data) return null;

        return purchaseOrderMapper.toDomain(data);
    }

    // =========================
    // UPDATE
    // =========================

    async update(
        data: Partial<PurchaseOrderWithItems>,
    ): Promise<void> {
        if (!data.purchaseOrder?.id) {
            throw new Error("PurchaseOrder id is required");
        }

        const dto = purchaseOrderMapper.toUpdateDTO(
            data as PurchaseOrderWithItems,
        );

        await this.remote.updatePurchaseOrder(
            data.purchaseOrder.id,
            dto,
        );
    }

    // =========================
    // STATUS UPDATE
    // =========================

    async updateStatus(
        id: string,
        status: PurchaseOrderStatusType,
    ): Promise<void> {
        await this.remote.updatePurchaseOrderStatus(id, status);
    }

    // =========================
    // DELETE
    // =========================

    async delete(id: string): Promise<void> {
        await this.remote.deletePurchaseOrder(id);
    }
}