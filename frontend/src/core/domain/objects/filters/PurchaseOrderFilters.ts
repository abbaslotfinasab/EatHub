import type {PurchaseOrderStatusType} from "../../entities/inventory/facture/PurchaseOrder.ts";

export interface PurchaseOrderFilters {
    supplierId?: string;
    status?: PurchaseOrderStatusType;
    fromDate?: string;   // ISO date
    toDate?: string;
}