import { useFormContext } from "react-hook-form";

import type { OrderFormInput } from "./OrderFormInput";

export const useOrderForm = () => {
    const methods = useFormContext<OrderFormInput>();

    const orderItems = methods.watch("orderItems");

    const itemCount = orderItems.length;

    const totalQuantity = orderItems.reduce(
        (sum, item) => sum + item.quantity,
        0,
    );

    return {
        ...methods,

        orderItems,
        itemCount,
        totalQuantity,
    };
};