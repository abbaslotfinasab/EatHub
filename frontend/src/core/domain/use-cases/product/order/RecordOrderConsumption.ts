import type {OrderRepository} from "../../../repositories/product/OrderRepository.ts";
import type {
    RecordOrderConsumptionInput,
    RecordOrderConsumptionResult,
} from "../../../entities/product/order/OrderInventoryConsumption.ts";

export class RecordOrderConsumption {
    constructor(private readonly repository: OrderRepository) {}

    execute(input: RecordOrderConsumptionInput): Promise<RecordOrderConsumptionResult> {
        if (!input.orderId) throw new Error("شناسه سفارش معتبر نیست");
        if (!input.idempotencyKey) throw new Error("کلید ثبت تکرار لازم است");
        if (input.lines.length === 0) throw new Error("حداقل یک ردیف مصرف لازم است");
        return this.repository.recordConsumption(input);
    }
}
