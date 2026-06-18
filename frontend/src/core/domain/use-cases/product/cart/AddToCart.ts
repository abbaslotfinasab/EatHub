// core/application/use-cases/cart/AddToCart.ts
import { z } from 'zod';
import type { CartRepository } from '../../../repositories/product/CartRepository';

const AddToCartSchema = z.object({
    menuItemId: z.string(),
    quantity: z.number().positive(),
    notes: z.string().nullable().optional(),
});

export class AddToCart {
    constructor(private cartRepo: CartRepository) {}

    async execute(input: z.infer<typeof AddToCartSchema>) {
        const validated = AddToCartSchema.parse(input);
        return this.cartRepo.addItem(validated); // برگرداندن سبد جدید
    }
}