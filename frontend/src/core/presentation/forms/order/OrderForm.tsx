// presentation/forms/order/OrderForm.tsx

import type {OrderWithItems} from "../../../domain/entities/product/order/OrderWithItems";

import {OrderFormContent} from "./OrderFormContent";
import {type OrderFormInput, OrderFormSchema} from "./OrderFormInput.ts";
import {useForm} from "react-hook-form";
import {FormProvider} from "react-hook-form";
import {zodResolver} from "@hookform/resolvers/zod";
import {OrderFormMapper} from "./OrderFormMapper.tsx";
import {useEffect, useState} from "react";
import type {OrderItem} from "../../../domain/entities/product/order/OrderItem";

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
        defaultValues: {
            customerId: undefined,
            tableId: null,
            orderType: "dine_in",
            notes: "",
            orderItems: [],
        },
    });

    const [removedHistoricalKeys, setRemovedHistoricalKeys] = useState<Set<string>>(
        new Set(),
    );

    const historicalItems = (order?.orderItems ?? []).filter((item) => {
        const key = `${item.id ?? "unknown"}-${item.orderId}`;
        return item.menuItemId === null && !removedHistoricalKeys.has(key);
    });

    useEffect(() => {
        if (order) {
            methods.reset(OrderFormMapper.toForm(order));
        }
    }, [order, methods]);

    const handleRemoveHistorical = (item: OrderItem) => {
        const key = `${item.id ?? "unknown"}-${item.orderId}`;
        setRemovedHistoricalKeys((current) => {
            const next = new Set(current);
            next.add(key);
            return next;
        });
        methods.clearErrors("root");
    };

    return (
        <FormProvider {...methods}>
            <form
                onSubmit={methods.handleSubmit(
                    (data) => {
                        if (historicalItems.length > 0) {
                            methods.setError("root", {
                                type: "manual",
                                message:
                                    "آیتم‌های تاریخی را با آیتم‌های فعلی جایگزین کنید.",
                            });
                            return;
                        }

                        onSubmit(data);
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
                    historicalItems={historicalItems}
                    onRemoveHistorical={handleRemoveHistorical}
                />
            </form>
        </FormProvider>
    );
};
