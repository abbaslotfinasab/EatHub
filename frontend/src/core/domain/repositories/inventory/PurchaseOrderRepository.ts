import type {PurchaseOrderStatusType} from "../../entities/inventory/facture/PurchaseOrder.ts";
import type {PurchaseOrderFilters} from "../../objects/filters/PurchaseOrderFilters.ts";
import type {PurchaseOrderWithItems} from "../../entities/inventory/facture/PurchaseOrderWithItems.ts";



export interface PurchaseOrderRepository {
    create(input: PurchaseOrderWithItems): Promise<void>;

    findById(id: string): Promise<PurchaseOrderWithItems | null>;
    findAll(filters?: PurchaseOrderFilters): Promise<PurchaseOrderWithItems[]>;
    update(data: Partial<PurchaseOrderWithItems>): Promise<void>;
    updateStatus(id: string, status: PurchaseOrderStatusType): Promise<void>;
    delete(id: string): Promise<void>;
}