import type {OrderRepository} from "../../../repositories/product/OrderRepository.ts";
import type {OrderConsumptionRequirements} from "../../../entities/product/order/OrderInventoryConsumption.ts";

export class GetOrderConsumptionRequirements {
    constructor(private readonly repository: OrderRepository) {}

    execute(orderId: string): Promise<OrderConsumptionRequirements> {
        if (!orderId) throw new Error("شناسه سفارش معتبر نیست");
        return this.repository.getConsumptionRequirements(orderId);
    }
}
