import {z} from "zod";

export const OrderItemSchema = z.object({
    menuItemId: z.number(),
    quantity: z.number().positive(),
    notes: z.string().nullable().optional(),
});


export type OrderFormItemInput = z.infer<typeof OrderItemSchema>;
