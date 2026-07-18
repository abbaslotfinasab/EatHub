// presentation/components/order/OrderInfoCard.tsx

import {
    Card,
    CardContent,
    Divider,
    Stack,
    TextField,
    Typography,
} from "@mui/material";

import { Controller } from "react-hook-form";

import { useOrderForm } from "../../forms/order/useOrderForm";

import { CustomerAutocomplete } from "./CustomerAutocomplete/CustomerAutocomplete";
import { OrderTypeSelector } from "./OrderTypeSelector/OrderTypeSelector";

export const OrderInfoCard = () => {

    const {
        control,
        watch,
    } = useOrderForm();

    const orderType =
        watch("orderType");

    return (

        <Card
            elevation={0}
            sx={{
                borderRadius: 3,
                border: "1px solid",
                borderColor: "divider",
            }}
        >

            <CardContent>

                <Stack spacing={3}>

                    <Typography
                        variant="h6"
                        sx={{
                            fontWeight: 700,
                        }}
                    >
                        اطلاعات سفارش
                    </Typography>

                    <Divider />

                    <OrderTypeSelector />

                    <CustomerAutocomplete />

                    {orderType === "dine_in" && (

                        <Controller
                            control={control}
                            name="tableId"
                            render={({ field }) => (

                                <TextField
                                    {...field}
                                    label="شماره میز"
                                    value={field.value ?? ""}
                                />

                            )}
                        />

                    )}

                    <Controller
                        control={control}
                        name="notes"
                        render={({ field }) => (

                            <TextField
                                {...field}
                                label="توضیحات سفارش"
                                multiline
                                minRows={4}
                                value={field.value ?? ""}
                            />

                        )}
                    />

                </Stack>

            </CardContent>

        </Card>

    );

};