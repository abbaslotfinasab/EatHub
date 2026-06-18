import type {PurchaseOrder, PurchaseOrderStatusType} from "../../entities/inventory/PurchaseOrder.ts";

export interface PurchaseOrderFilters {
    supplierId?: string;
    status?: PurchaseOrderStatusType;
    fromDate?: string;   // ISO date
    toDate?: string;
}

export interface PurchaseOrderRepository {
    save(order: PurchaseOrder): Promise<void>;
    createWithItems(data: {
        supplierId: string;
        expectedDeliveryDate?: string | null;
        invoiceNumber?: string | null;
        notes?: string | null;
        items: Array<{
            ingredientId: string;
            quantity: number;
            unitPrice: number;
        }>;
    }): Promise<PurchaseOrder>; // یا Promise<void>
    findById(id: string): Promise<PurchaseOrder | null>;
    findAll(filters?: PurchaseOrderFilters): Promise<PurchaseOrder[]>;
    update(id: string, data: Partial<PurchaseOrder>): Promise<PurchaseOrder>;
    updateWithItems(
        id: string,
        data: {
            supplierId?: string;
            expectedDeliveryDate?: string | null;
            invoiceNumber?: string | null;
            notes?: string | null;
            status?: PurchaseOrderStatusType;
            items?: Array<{
                ingredientId: string;
                quantity: number;
                unitPrice: number;
            }>;
        }
    ): Promise<void>;
    updateStatus(id: string, status: PurchaseOrderStatusType): Promise<void>;
    delete(id: string): Promise<void>;
}