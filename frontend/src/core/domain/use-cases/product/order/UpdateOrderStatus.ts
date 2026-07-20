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


        if (!input.status) {

            throw new Error(
                "Order status is required",
            );

        }


        if (!input.paymentStatus) {

            throw new Error(
                "Payment status is required",
            );

        }


        if (!input.paymentMethod) {

            throw new Error(
                "Payment method is required",
            );

        }


        return this.repository.updateStatus(
            input,
        );

    }

}