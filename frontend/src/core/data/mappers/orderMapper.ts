import type {OrderDTO} from "../dtos/order/OrderDTO";
import type {OrderItemDTO} from "../dtos/order/OrderItemDTO";

import type {CreateOrderDTO} from "../dtos/order/CreateOrderDTO";
import type {CreateOrderItemDTO} from "../dtos/order/CreateOrderItemDTO";

import type {UpdateOrderDTO} from "../dtos/order/UpdateOrderDTO";
import type {UpdateOrderItemDTO} from "../dtos/order/UpdateOrderItemDTO";
import type {OrderWithItems} from "../../domain/entities/product/order/OrderWithItems";
import type {Order} from "../../domain/entities/product/order/Order";
import type {OrderItem} from "../../domain/entities/product/order/OrderItem.ts";


export const orderMapper = {
    // =====================================================
    // DTO -> DOMAIN
    // =====================================================

    toDomain(dto: OrderDTO): OrderWithItems {
        return {
            order: orderMapper.toOrder(dto),
            orderItems: (dto.items ?? []).map(orderMapper.toOrderItem),
        };
    },

    toOrder(dto: OrderDTO): Order {
        return {
            id: dto.id,
            customerId: dto.customer_id ?? undefined,
            customerName: dto.customer_name ?? undefined,
            customerPhone: dto.customer_phone ?? undefined,
            tableId: dto.table,
            orderType: dto.order_type,
            status: dto.status as Order["status"],
            subtotal: dto.subtotal,
            discount: dto.discount,
            tax: dto.tax,
            totalAmount: dto.total_amount,
            paymentStatus: dto.payment_status as Order["paymentStatus"],
            paymentMethod : dto.payment_method as Order["paymentMethod"],
            notes: dto.notes,
            createdAt: dto.created_at,
            updatedAt: dto.updated_at,
        };
    },

    toOrderItem(dto: OrderItemDTO): OrderItem {
        return {
            id: dto.id,
            orderId: dto.order_id,
            menuItemId: dto.menu_item_id,
            menuItemName: dto.menu_item_name,
            quantity: dto.quantity,
            unitPrice: dto.unit_price,
            totalPrice: dto.total_price,
            notes: dto.notes,
            createdAt: dto.created_at,
            updatedAt: dto.updated_at,
        };
    },

    // =====================================================
    // DOMAIN -> CREATE DTO
    // =====================================================

    toCreateDTO(domain: OrderWithItems): CreateOrderDTO {
        return {
            customer_id: domain.order.customerId,
            table: domain.order.tableId,
            order_type: domain.order.orderType,
            notes: domain.order.notes,
            items: domain.orderItems.map(orderMapper.toCreateOrderItemDTO),
        };
    },

    toCreateOrderItemDTO(item: OrderItem): CreateOrderItemDTO {
        return {
            menu_item_id: item.menuItemId,
            quantity: item.quantity,
            notes: item.notes,
        };
    },

    // =====================================================
    // DOMAIN -> UPDATE DTO
    // =====================================================

    toUpdateDTO(domain: OrderWithItems): UpdateOrderDTO {
        return {
            customer_id: domain.order.customerId,
            table_id: domain.order.tableId,
            order_type: domain.order.orderType,
            notes: domain.order.notes,
            items: domain.orderItems.map(orderMapper.toUpdateOrderItemDTO),
        };
    },

    toUpdateOrderItemDTO(item: OrderItem): UpdateOrderItemDTO {
        return {
            id: item.id,
            menu_item_id: item.menuItemId,
            quantity: item.quantity,
            notes: item.notes,
        };
    },
};