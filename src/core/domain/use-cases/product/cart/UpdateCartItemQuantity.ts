// core/application/use-cases/cart/UpdateCartItemQuantity.ts
import { z } from 'zod';
import type { CartRepository } from '../../../repositories/product/CartRepository';

const UpdateQuantitySchema = z.object({
    cartItemId: z.string(),
    quantity: z.number().positive(),
});

export class UpdateCartItemQuantity {
    constructor(private cartRepo: CartRepository) {}

    async execute(input: z.infer<typeof UpdateQuantitySchema>) {
        const { cartItemId, quantity } = UpdateQuantitySchema.parse(input);
        return this.cartRepo.updateItemQuantity(cartItemId, quantity);
    }
}