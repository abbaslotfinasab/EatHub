// presentation/components/order/OrderTypeSelector/OrderTypeSelector.tsx

import { Controller } from "react-hook-form";

import {
    Stack,
    Typography,
} from "@mui/material";

import { useOrderForm } from "../../../forms/order/useOrderForm";

import { ORDER_TYPES } from "./orderTypes";
import { OrderTypeCard } from "./OrderTypeCard";

export const OrderTypeSelector = () => {

    const { control } = useOrderForm();

    return (

        <Controller
            name="orderType"
            control={control}
            render={({ field }) => (

                <Stack spacing={2}>

                    <Typography
                        sx={{
                            fontWeight: 700,
                            fontSize: 15,
                        }}
                    >
                        نوع سفارش
                    </Typography>

                    <Stack
                        sx={{
                            flexDirection: {
                                xs: "column",
                                sm: "row",
                            },

                            gap: 2,
                        }}
                    >

                        {ORDER_TYPES.map((type) => (

                            <OrderTypeCard
                                key={type.value}
                                title={type.title}
                                description={type.description}
                                icon={type.icon}
                                selected={
                                    field.value ===
                                    type.value
                                }
                                onClick={() =>
                                    field.onChange(
                                        type.value,
                                    )
                                }
                            />

                        ))}

                    </Stack>

                </Stack>

            )}
        />

    );

};