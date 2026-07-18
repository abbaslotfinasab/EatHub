// core/application/use-cases/order/CreateOrder.ts
import type { OrderRepository } from '../../../repositories/product/OrderRepository';
import type {OrderWithItems} from "../../../entities/product/order/OrderWithItems.ts";




export class CreateOrder {
    constructor(private orderRepo: OrderRepository){}

    async execute(input: OrderWithItems) {

        await this.orderRepo.create(input);
    }
}