import type {UpdateOrderStatusInput} from "../../../entities/product/order/UpdateOrderStatusInput";
import type {OrderRepository} from "../../../repositories/product/OrderRepository.ts";


export class UpdateOrderStatus {


    constructor(
        private readonly repository: OrderRepository,
    ) {
    }


    async execute(
        input: UpdateOrderStatusInput,
    ): Promise<void> {


        if (!input.orderId) {

            throw new Error(
                "Order id is required",
            );

        }


        if (!input.status && !input.paymentStatus && !input.paymentMethod) {
            throw new Error("At least one order field is required");
        }


        return this.repository.updateStatus(
            input,
        );

    }

}
