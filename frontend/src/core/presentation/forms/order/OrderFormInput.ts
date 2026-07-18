import {z} from "zod";
import {OrderItemSchema} from "./OrderFormItemInput.ts";

export const OrderFormSchema = z.object({
    customerId: z.number().optional(),

    tableId: z.string().nullable().optional(),

    orderType: z.enum([
        "dine_in",
        "takeaway",
        "delivery",
    ]),

    orderItems: z.array(OrderItemSchema).min(1),

    notes: z.string().nullable().optional(),

    discount: z.number().default(0).optional(),

    tax: z.number().default(0).optional(),
});

export type OrderFormInput = z.infer<typeof OrderFormSchema>;
