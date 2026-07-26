import { z } from "zod";

export const OrderStatusFormSchema = z.object({

    status: z.enum([
        "pending",
        "confirmed",
        "preparing",
        "ready",
        "completed",
        "cancelled",
    ]),

    paymentStatus: z.enum([
        "pending",
        "unpaid",
        "paid",
        "failed",
        "refunded",
    ]),

    paymentMethod: z.enum([
        "cash",
        "card",
        "customer_account",
    ]),

});

export type OrderStatusFormInput =
    z.infer<typeof OrderStatusFormSchema>;