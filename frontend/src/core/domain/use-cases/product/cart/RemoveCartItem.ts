// core/application/use-cases/cart/RemoveCartItem.ts
import { z } from 'zod';
import type { CartRepository } from '../../../repositories/product/CartRepository';

const RemoveCartItemSchema = z.object({
    cartItemId: z.string(),
});

export class RemoveCartItem {
    constructor(private cartRepo: CartRepository) {}

    async execute(input: z.infer<typeof RemoveCartItemSchema>) {
        const { cartItemId } = RemoveCartItemSchema.parse(input);
        return this.cartRepo.removeItem(cartItemId);
    }
}