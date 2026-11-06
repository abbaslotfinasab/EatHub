import type {
    CreateGoodsReceiptInput,
    CreatePurchaseOrderInput,
    GoodsReceipt,
    PurchaseSupplierSummary,
    ReceivingPurchaseOrder,
    UpdatePurchaseOrderInput,
} from '../../entities/inventory/facture/PurchaseReceiving.ts';

export interface PurchaseReceivingRepository {
    listOrders(): Promise<ReceivingPurchaseOrder[]>;
    getOrder(id: string): Promise<ReceivingPurchaseOrder>;
    createOrder(input: CreatePurchaseOrderInput): Promise<ReceivingPurchaseOrder>;
    updateOrder(id: string, input: UpdatePurchaseOrderInput): Promise<ReceivingPurchaseOrder>;
    sendOrder(id: string): Promise<ReceivingPurchaseOrder>;
    cancelOrder(id: string): Promise<ReceivingPurchaseOrder>;
    listReceipts(orderId: string): Promise<GoodsReceipt[]>;
    createReceipt(input: CreateGoodsReceiptInput): Promise<GoodsReceipt>;
    listSuppliers(): Promise<PurchaseSupplierSummary[]>;
}
