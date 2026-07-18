import type {PurchaseOrderItem} from "./PurchaseOrderItem.ts";
import type {PurchaseOrder} from "./PurchaseOrder.ts";


export interface PurchaseOrderWithItems {
    purchaseOrder: PurchaseOrder;
    items: PurchaseOrderItem[];
}