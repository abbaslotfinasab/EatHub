// core/application/use-cases/order/GetAllOrdersWithItems.ts
import type { OrderRepository } from '../../../repositories/product/OrderRepository';
import type {OrderWithItems} from "../../../entities/product/order/OrderWithItems.ts";

export class GetAllOrdersWithItems {
    constructor(private orderRepository: OrderRepository) {}

    async execute(): Promise<OrderWithItems[]> {
        return this.orderRepository.findAll();
    }
}