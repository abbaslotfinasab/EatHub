// core/application/use-cases/order/CreateOrder.ts
import { z } from 'zod';
import type { OrderRepository } from '../../../repositories/product/OrderRepository';


const OrderItemSchema = z.object({
    orderId: z.string(),
    menuItemId: z.string(),
    quantity: z.number().positive(),
    notes: z.string().nullable().optional(),
});

const CreateOrderSchema = z.object({
    customerId: z.string().min(1).optional(),
    customerName: z.string().min(1).optional(),
    customerPhone: z.string().optional(),
    tableId: z.string().nullable().optional(),
    orderType: z.enum(["dine_in", "takeaway", "delivery"]) ,
    items: z.array(OrderItemSchema).min(1),
    notes: z.string().nullable().optional(),
});


export type CreateOrderInput = z.infer<typeof CreateOrderSchema>;

export class CreateOrder {
    constructor(private orderRepo: OrderRepository){}

    async execute(input: CreateOrderInput) {
        const validated = CreateOrderSchema.parse(input);


        const { items, ...orderDate } = validated;


        await this.orderRepo.create(orderDate,items);
    }
}