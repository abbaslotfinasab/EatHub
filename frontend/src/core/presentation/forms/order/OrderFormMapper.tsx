// presentation/forms/order/OrderFormMapper.ts

import type {Order} from "../../../domain/entities/product/order/Order";
import type {OrderItem} from "../../../domain/entities/product/order/OrderItem";
import type {OrderWithItems} from "../../../domain/entities/product/order/OrderWithItems";

import type {OrderFormInput} from "./OrderFormInput";

import {OrderStatus} from "../../../domain/entities/product/order/Order";

export const OrderFormMapper = {

    // ==========================
    // Form -> Domain
    // ==========================

    toDomain(
        input: OrderFormInput,
    ): OrderWithItems {

        const order: Order = {
            id: "",

            customerId: input.customerId,

            tableId:
                input.tableId
                    ? Number(input.tableId)
                    : null,

            orderType:
            input.orderType,

            status:
            OrderStatus.PENDING,

            subtotal: 0,

            discount: 0,

            tax: 0,

            totalAmount: 0,

            paymentStatus: "pending",

            notes:
                input.notes ?? null,
        };

        const orderItems: OrderItem[] =
            input.orderItems.map((item) => ({
                id: -1,

                orderId: -1,

                menuItemId: item.menuItemId,

                quantity: item.quantity,

                notes:
                    item.notes ?? null,
            }));

        return {
            order,
            orderItems,
        };
    },

    // ==========================
    // Domain -> Form
    // ==========================

    toForm(
        data: OrderWithItems,
    ): OrderFormInput {

        const invalidItem = data.orderItems.find(
            (item) => item.menuItemId == null,
        );

        if (invalidItem) {
            throw new Error(
                "Historical order items must be replaced or removed before saving.",
            );
        }

        return {

            customerId:
            data.order.customerId,

            tableId:
                data.order.tableId?.toString(),

            orderType:
            data.order.orderType,

            notes:
                data.order.notes ?? null,

            discount: 0,
            tax: 0,

            orderItems:
            data.orderItems
                .map((item) => {
                    if (item.menuItemId == null) {
                        throw new Error(
                            "Historical order items must be replaced or removed before saving.",
                        );
                    }

                    return {
                        menuItemId: item.menuItemId,
                        quantity: item.quantity,
                        notes: item.notes ?? null,
                    };
                }),
        };
    },

};
