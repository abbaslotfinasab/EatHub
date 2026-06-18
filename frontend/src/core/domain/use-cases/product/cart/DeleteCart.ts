// core/application/use-cases/cart/DeleteCart.ts
import { z } from 'zod';
import type { CartRepository } from '../../../repositories/product/CartRepository';

const DeleteCartSchema = z.object({
    cartId: z.string(),
});

export class DeleteCart {
    constructor(private cartRepo: CartRepository) {}

    async execute(input: z.infer<typeof DeleteCartSchema>) {
        const { cartId } = DeleteCartSchema.parse(input);
        return this.cartRepo.delete(cartId);
    }
}