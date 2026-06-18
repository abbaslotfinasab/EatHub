// core/application/use-cases/cart/GetActiveCart.ts
import type { CartRepository } from '../../../repositories/product/CartRepository';

export class GetActiveCart {
    constructor(private cartRepo: CartRepository) {}

    async execute() {
        return this.cartRepo.getActive();
    }
}