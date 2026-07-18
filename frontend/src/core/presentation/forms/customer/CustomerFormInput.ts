// presentation/forms/customer/CustomerFormInput.ts

import { z } from "zod";

export const CustomerFormSchema = z.object({

    name: z
        .string()
        .trim()
        .min(2),

    phone: z
        .string()
        .trim()
        .min(10),

});

export type CustomerFormInput =
    z.infer<typeof CustomerFormSchema>;