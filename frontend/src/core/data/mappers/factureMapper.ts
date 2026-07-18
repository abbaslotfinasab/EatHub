import type {PurchaseOrder} from "../../domain/entities/inventory/facture/PurchaseOrder";
import type {PurchaseOrderWithItems} from "../../domain/entities/inventory/facture/PurchaseOrderWithItems";
import type {PurchaseOrderDTO} from "../dtos/facture/PurchaseOrderDTO";
import type {CreatePurchaseOrderDTO} from "../dtos/facture/CreatePurchaseOrderDTO.ts";
import type {PurchaseOrderItem} from "../../domain/entities/inventory/facture/PurchaseOrderItem.ts";
import type {UpdatePurchaseOrderDTO} from "../dtos/facture/UpdatePurchaseOrderDTO.ts";
import type {PurchaseOrderItemDTO} from "../dtos/facture/PurchaseOrderItemDTO.ts";
import type {CreatePurchaseOrderItemDTO} from "../dtos/facture/CreatePurchaseOrderItemDTO.ts";
import type {UpdatePurchaseOrderItemDTO} from "../dtos/facture/UpdatePurchaseOrderItemDTO.ts";


export const purchaseOrderMapper = {

    // =====================================================
    // DTO -> DOMAIN
    // =====================================================

    toDomain(dto: PurchaseOrderDTO): PurchaseOrderWithItems {
        return {
            purchaseOrder: purchaseOrderMapper.toPurchaseOrder(dto),
            items: (dto.items ?? []).map(purchaseOrderMapper.toPurchaseOrderItem),
        };
    },

    toPurchaseOrder(dto: PurchaseOrderDTO): PurchaseOrder {
        return {
            id: dto.id,

            // فعلاً supplier_name را نگاشت می‌کنیم
            supplierId: dto.supplier_id,
            supplierName: dto.supplier_name,
            supplierNumber: dto.supplier_number,

            type: dto.type,

            status: dto.status as PurchaseOrder["status"],

            subtotal: dto.subtotal,
            tax: dto.tax,
            discount: dto.discount,

            totalAmount: dto.total_amount,
            invoiceNumber: dto.invoice_number,
            notes: dto.notes,

            createdAt: dto.created_at,
            updatedAt: dto.updated_at,
        };
    },

    toPurchaseOrderItem(dto: PurchaseOrderItemDTO): PurchaseOrderItem {
        return {
            id: dto.id,
            purchaseOrderId: dto.purchase_order_id,
            componentId: dto.component_id,
            quantity: dto.quantity,
            unitPrice: dto.unit_price,
            totalPrice: dto.total_price,
            createdAt: dto.created_at,
            updatedAt: dto.updated_at,
        };
    },

    // =====================================================
    // DOMAIN -> CREATE DTO
    // =====================================================

    toCreateDTO(domain: PurchaseOrderWithItems): CreatePurchaseOrderDTO {
        return {
            supplier_id: domain.purchaseOrder.supplierId,

            supplier_name: domain.purchaseOrder.supplierName,

            supplier_number: domain.purchaseOrder.supplierNumber,

            status: domain.purchaseOrder.status ?? "draft",

            subtotal: domain.purchaseOrder.subtotal,
            tax: domain.purchaseOrder.tax,
            discount: domain.purchaseOrder.discount,


            total_amount: domain.purchaseOrder.totalAmount,

            invoice_number: domain.purchaseOrder.invoiceNumber,

            notes: domain.purchaseOrder.notes,

            items: domain.items.map(
                purchaseOrderMapper.toCreatePurchaseOrderItemDTO
            ),
        };
    },

    toCreatePurchaseOrderItemDTO(
        item: PurchaseOrderItem
    ): CreatePurchaseOrderItemDTO {
        return {
            ingredient_id: item.componentId,
            quantity: item.quantity,
            unit_price: item.unitPrice,
            total_price: item.totalPrice,
        };
    },

    // =====================================================
    // DOMAIN -> UPDATE DTO
    // =====================================================

    toUpdateDTO(domain: PurchaseOrderWithItems): UpdatePurchaseOrderDTO {
        return {
            id: domain.purchaseOrder.id ?? "",

            supplier_id: domain.purchaseOrder.supplierId,

            supplier_name: domain.purchaseOrder.supplierName,

            supplier_number: domain.purchaseOrder.supplierNumber,

            status: domain.purchaseOrder.status ?? "draft",

            subtotal: domain.purchaseOrder.subtotal,
            tax: domain.purchaseOrder.tax,
            discount: domain.purchaseOrder.discount,

            total_amount: domain.purchaseOrder.totalAmount,


            invoice_number: domain.purchaseOrder.invoiceNumber,

            notes: domain.purchaseOrder.notes,

            items: domain.items.map(
                purchaseOrderMapper.toUpdatePurchaseOrderItemDTO
            ),
        };
    },

    toUpdatePurchaseOrderItemDTO(
        item: PurchaseOrderItem
    ): UpdatePurchaseOrderItemDTO {
        return {
            id: item.id,
            ingredient_id: item.componentId,
            quantity: item.quantity,
            unit_price: item.unitPrice,
            total_price: item.totalPrice,
        };
    },
};