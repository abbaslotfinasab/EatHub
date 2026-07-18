import {z} from "zod";
import {PurchaseOrderItemSchema} from "./PurchaseOrderFormItemInput.ts";

export const CreatePurchaseOrderSchema = z.object({
    supplierId: z.string().min(1, 'شناسه تأمین‌کننده الزامی است'),
    expectedDeliveryDate: z.string().nullable().optional(),
    invoiceNumber: z.string().nullable().optional(),
    notes: z.string().nullable().optional(),
    items: z.array(PurchaseOrderItemSchema).min(1, 'حداقل یک آیتم باید وجود داشته باشد'),
});

export type CreatePurchaseOrderWithItemsInput = z.infer<typeof CreatePurchaseOrderSchema>;

