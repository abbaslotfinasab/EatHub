import { z } from "zod";

const quantitySchema = z.string()
    .trim()
    .regex(/^\d{1,24}(?:\.\d{1,12})?$/, "مقدار باید حداکثر ۲۴ رقم صحیح و ۱۲ رقم اعشار داشته باشد")
    .refine((value) => /[1-9]/.test(value), "مقدار باید بزرگ‌تر از صفر باشد");

const recipeLineSchema = z.object({
    ingredientId: z.string().min(1, "یک ماده اولیه انتخاب کنید"),
    ingredientName: z.string().optional(),
    materialId: z.null().optional(),
    quantity: quantitySchema,
    unit: z.enum(["kg", "g", "l", "ml", "pc", "pk"]),
    notes: z.string().nullable().optional(),
});

const recipeOutputSchema = recipeLineSchema.extend({
    isPrimary: z.boolean().default(false),
});

export const RecipeFormSchema = z.object({
    name: z.string().trim().min(1, "نام رسپی الزامی است"),
    description: z.string().nullable().optional(),
    ingredients: z.array(recipeLineSchema),
    outputs: z.array(recipeOutputSchema),
}).superRefine((values, context) => {
    if (values.outputs.filter((line) => line.isPrimary).length > 1) {
        context.addIssue({
            code: "custom",
            path: ["outputs"],
            message: "حداکثر یک محصول خروجی می‌تواند محصول اصلی باشد",
        });
    }
});

export type RecipeFormValues = z.infer<typeof RecipeFormSchema>;
export type RecipeFormInput = z.input<typeof RecipeFormSchema>;
