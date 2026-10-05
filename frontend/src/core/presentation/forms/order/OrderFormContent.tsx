// presentation/forms/order/OrderFormContent.tsx

import {Stack} from "@mui/material";
import type {OrderItem} from "../../../domain/entities/product/order/OrderItem.ts";


import {OrderHeader} from "../../components/order/OrderHeader";
import {OrderInfoCard} from "../../components/order/OrderInfoCard";
import {OrderMenuPicker} from "../../components/order/OrderMenuPicker/OrderMenuPicker";
import {OrderSummaryCard} from "../../components/order/OrderSummaryCard.tsx";
import {SelectedOrderItems} from "../../components/order/SelectedOrderItems.tsx";

interface OrderFormContentProps {
    mode: "create" | "edit";
    loading?: boolean;
    onCancel?: () => void;
    historicalItems?: OrderItem[];
    onRemoveHistorical?: (item: OrderItem) => void;
}

export const OrderFormContent = ({
                                     mode,
                                     onCancel,
                                     historicalItems,
                                     onRemoveHistorical,
                                 }: OrderFormContentProps) => {

    return (
        <Stack
            spacing={3}
        >

            <OrderHeader
                mode={mode}
                onCancel={onCancel}
            />

            <OrderInfoCard/>

            <OrderMenuPicker/>

            <SelectedOrderItems
                historicalItems={historicalItems}
                onRemoveHistorical={onRemoveHistorical}
            />

            <OrderSummaryCard
                mode={mode}
                onCancel={onCancel}
            />

        </Stack>
    );
};
