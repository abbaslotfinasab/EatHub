import z from "zod";
import {MenuFormItemSchema} from "./MenuFormItemInput.ts";




export const MenuFormSchema = z.object({
    name: z.string().min(2),

    category: z.string().min(1),

    description: z.string().nullable(),

    sortOrder: z.number(),

    isActive: z.boolean(),

    items: z.array(MenuFormItemSchema),
});

export type MenuFormInput = z.infer<typeof MenuFormSchema>;

