// core/application/use-cases/cart/ClearCart.ts
import { z } from 'zod';
import type { CartRepository } from '../../../repositories/product/CartRepository';

const ClearCartSchema = z.object({
    cartId: z.string(),
});

export class ClearCart {
    constructor(private cartRepo: CartRepository) {}

    async execute(input: z.infer<typeof ClearCartSchema>) {
        const { cartId } = ClearCartSchema.parse(input);
        return this.cartRepo.clear(cartId);
    }
}