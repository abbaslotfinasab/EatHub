// شِمای هر آیتم از فاکتور
import {z} from "zod";

export const PurchaseOrderItemSchema = z.object({
    ingredientId: z.string().min(1, 'شناسه ماده اولیه الزامی است'),
    quantity: z.number().positive('مقدار باید مثبت باشد'),
    unitPrice: z.number().positive('قیمت واحد باید مثبت باشد'),
});
