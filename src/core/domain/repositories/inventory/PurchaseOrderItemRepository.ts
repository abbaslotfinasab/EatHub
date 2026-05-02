import type {PurchaseOrder} from "../../entities/inventory/PurchaseOrder.ts";
import type {PurchaseOrderItem} from "../../entities/inventory/PurchaseOrderItem.ts";

export interface PurchaseOrderItemRepository {
    save(item: PurchaseOrderItem): Promise<void>;
    findById(id: string): Promise<PurchaseOrderItem | null>;
    findAllByOrderId(orderId: string): Promise<PurchaseOrderItem[]>;
    update(id: string, data: Partial<PurchaseOrderItem>): Promise<PurchaseOrderItem>;
    delete(id: string): Promise<void>;
    deleteByOrderId(orderId: string): Promise<void>;  // حذف همه آیتم‌های یک فاکتور
}


export interface PurchaseOrderWithItems {
    order: PurchaseOrder;
    items: PurchaseOrderItem[];
}
