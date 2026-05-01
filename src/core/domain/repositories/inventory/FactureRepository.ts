// core/domain/repositories/PurchaseOrderRepository.ts
import type {PurchaseOrder, PurchaseOrderStatusType} from '../../entities/inventory/Facture';
import type {PurchaseOrderItem} from '../../entities/inventory/Facture';

export interface PurchaseOrderFilters {
    supplierId?: string;
    status?: PurchaseOrderStatusType;
    fromDate?: string;   // ISO date
    toDate?: string;
}

export interface PurchaseOrderRepository {
    save(order: PurchaseOrder): Promise<void>;
    findById(id: string): Promise<PurchaseOrder | null>;
    findAll(filters?: PurchaseOrderFilters): Promise<PurchaseOrder[]>;
    update(id: string, data: Partial<PurchaseOrder>): Promise<PurchaseOrder>;
    updateStatus(id: string, status: PurchaseOrderStatusType): Promise<void>;
    delete(id: string): Promise<void>;
}


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

export interface PurchaseOrderAggregateRepository {
    findWithItemsById(id: string): Promise<PurchaseOrderWithItems | null>;
    saveWithItems(order: PurchaseOrder, items: PurchaseOrderItem[]): Promise<void>;
    updateWithItems(orderId: string, orderData: Partial<PurchaseOrder>, items: PurchaseOrderItem[]): Promise<void>;
}