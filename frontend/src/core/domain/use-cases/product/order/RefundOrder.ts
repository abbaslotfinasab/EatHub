import type {RefundOrderInput, RefundOrderResult} from "../../../entities/product/order/RefundOrderInput.ts";
import type {OrderRepository} from "../../../repositories/product/OrderRepository.ts";

export class RefundOrder {
    constructor(private readonly repository: OrderRepository) {}

    execute(input: RefundOrderInput): Promise<RefundOrderResult> {
        if (!input.orderId || !input.idempotencyKey || !input.reason.trim()) {
            throw new Error("Order, idempotency key, and refund reason are required");
        }
        return this.repository.refund(input);
    }

    getResult(orderId: string): Promise<RefundOrderResult> {
        if (!orderId) {
            throw new Error("Order id is required");
        }
        return this.repository.getRefund(orderId);
    }
}
