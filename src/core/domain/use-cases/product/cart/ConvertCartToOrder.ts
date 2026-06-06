// core/application/use-cases/cart/CheckoutCart.ts
import { z } from 'zod';
import type { CartRepository } from '../../../repositories/product/CartRepository';

const CheckoutCartSchema = z.object({
    cartId: z.string(),
});

export class CheckoutCart {
    constructor(private cartRepo: CartRepository) {}

    async execute(input: z.infer<typeof CheckoutCartSchema>) {
        const { cartId } = CheckoutCartSchema.parse(input);
        return this.cartRepo.checkout(cartId);
    }
}