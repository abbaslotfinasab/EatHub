// core/application/use-cases/order/GetAllOrdersWithItems.ts
import type { OrderRepository } from '../../../repositories/product/OrderRepository';
import type { OrderFilters } from '../../../objects/filters/OrderFilters'; // یا مسیر صحیح فیلترها
import type {OrderResult} from "../../../entities/product/OrderResult.ts";

export class GetAllOrdersWithItems {
    constructor(private orderRepository: OrderRepository) {}

    async execute(filters?: OrderFilters): Promise<OrderResult[]> {
        return this.orderRepository.findAll(filters);
    }
}