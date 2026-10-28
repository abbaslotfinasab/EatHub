import type {
    CreateGoodsReceiptInput,
    GoodsReceipt,
    PurchaseSupplierSummary,
    ReceivingPurchaseOrder,
} from '../../entities/inventory/facture/PurchaseReceiving.ts';

export interface PurchaseReceivingRepository {
    listOrders(): Promise<ReceivingPurchaseOrder[]>;
    getOrder(id: string): Promise<ReceivingPurchaseOrder>;
    listReceipts(orderId: string): Promise<GoodsReceipt[]>;
    createReceipt(input: CreateGoodsReceiptInput): Promise<GoodsReceipt>;
    listSuppliers(): Promise<PurchaseSupplierSummary[]>;
}
