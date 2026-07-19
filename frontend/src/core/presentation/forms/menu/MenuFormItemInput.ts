import {z} from "zod";

export const MenuFormItemSchema = z.object({
    id: z.string().optional(),

    name: z.string().min(2),

    description: z.string().nullable(),

    price: z.number().positive(),

    imageUrl: z.string().nullable(),

    isAvailable: z.boolean(),

});

export type MenuFormItemInput = z.infer<typeof MenuFormItemSchema>;

