// presentation/forms/order/OrderForm.tsx

import type {OrderWithItems} from "../../../domain/entities/product/order/OrderWithItems";

import {OrderFormContent} from "./OrderFormContent";
import {type OrderFormInput, OrderFormSchema} from "./OrderFormInput.ts";
import { useForm } from "react-hook-form";
import { FormProvider } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {OrderFormMapper} from "./OrderFormMapper.tsx";

interface OrderFormProps {
    mode: "create" | "edit";

    order?: OrderWithItems;

    loading?: boolean;

    onSubmit(
        values: OrderFormInput,
    ): Promise<void> | void;

    onCancel?(): void;
}



export const OrderForm = ({
    mode,
    order,
    loading,
    onSubmit,
    onCancel,
}: OrderFormProps) => {

    const methods = useForm<OrderFormInput>({
        resolver: zodResolver(OrderFormSchema),
        defaultValues: order
            ? OrderFormMapper.toForm(order)
            : {
                  customerId: undefined,
                  tableId: null,
                  orderType: "dine_in",
                  notes: "",
                  orderItems: [],
              },
    });

    return (
        <FormProvider {...methods}>
           <form
    onSubmit={methods.handleSubmit(
        (data) => {
console.log(
    methods.formState.errors.orderItems?.[0]?.menuItemId
);            onSubmit(data);
        },
        (errors) => {
            console.log(errors);
        },
    )}
>
                <OrderFormContent
                    loading={loading}
                    mode={mode}
                    onCancel={onCancel}
                />
            </form>
        </FormProvider>
    );
};