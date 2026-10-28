import type { PurchaseReceivingRepository } from '../../domain/repositories/inventory/PurchaseReceivingRepository.ts';
import type {
    CreateGoodsReceiptInput,
    GoodsReceipt,
    PurchaseSupplierSummary,
    ReceivingPurchaseOrder,
} from '../../domain/entities/inventory/facture/PurchaseReceiving.ts';
import type {
    CreateGoodsReceiptDTO,
    GoodsReceiptReadDTO,
    PurchaseOrderReadDTO,
} from '../dtos/purchase/PurchaseReceivingDTO.ts';
import { PurchaseReceivingRemoteDataSource } from '../datasources/PurchaseReceivingRemoteDataSource.ts';

const mapOrder = (dto: PurchaseOrderReadDTO): ReceivingPurchaseOrder => ({
    id: String(dto.id),
    businessId: String(dto.business_id),
    supplierId: String(dto.supplier_id),
    status: dto.status,
    orderDate: dto.order_date,
    expectedDate: dto.expected_date,
    items: dto.items.map((item) => ({
        id: String(item.id),
        ingredientId: String(item.ingredient_id),
        orderedQuantity: item.quantity,
        unitPrice: item.unit_price,
        purchaseUnit: item.purchase_unit,
    })),
});

const mapReceipt = (dto: GoodsReceiptReadDTO): GoodsReceipt => ({
    id: String(dto.id),
    purchaseOrderId: String(dto.purchase_order_id),
    receivedDate: dto.received_date,
    notes: dto.notes,
    warehouseId: dto.warehouse_id === null ? null : String(dto.warehouse_id),
    items: dto.items.map((item) => ({
        id: String(item.id),
        purchaseOrderItemId: String(item.purchase_order_item_id),
        receivedQuantity: item.received_quantity,
        rejectedQuantity: item.rejected_quantity,
        purchaseUnit: item.purchase_unit,
    })),
});

export class PurchaseReceivingRepositoryImpl implements PurchaseReceivingRepository {
    constructor(private readonly remote = new PurchaseReceivingRemoteDataSource()) {}

    async listOrders(): Promise<ReceivingPurchaseOrder[]> {
        return (await this.remote.listOrders()).map(mapOrder);
    }

    async getOrder(id: string): Promise<ReceivingPurchaseOrder> {
        return mapOrder(await this.remote.getOrder(id));
    }

    async listReceipts(orderId: string): Promise<GoodsReceipt[]> {
        return (await this.remote.listReceipts(orderId)).map(mapReceipt);
    }

    async createReceipt(input: CreateGoodsReceiptInput): Promise<GoodsReceipt> {
        const payload: CreateGoodsReceiptDTO = {
            idempotency_key: input.idempotencyKey,
            purchase_order_id: Number(input.purchaseOrderId),
            received_date: input.receivedDate,
            notes: input.notes,
            warehouse_id: Number(input.warehouseId),
            items: input.items.map((item) => ({
                purchase_order_item_id: Number(item.purchaseOrderItemId),
                received_quantity: item.receivedQuantity,
                purchase_unit: item.purchaseUnit,
            })),
        };
        return mapReceipt(await this.remote.createReceipt(payload));
    }

    async listSuppliers(): Promise<PurchaseSupplierSummary[]> {
        return (await this.remote.listSuppliers()).map((supplier) => ({
            id: String(supplier.id),
            name: supplier.name,
        }));
    }
}
