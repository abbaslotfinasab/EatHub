import {useNavigate} from "react-router-dom";

import {
    Alert,
    Box,
    Container,
} from "@mui/material";


import {useCreateOrder} from "../../hooks/order/useCreateOrder";

import type {OrderFormInput} from "../../forms/order/OrderFormInput";
import {OrderForm} from "../../forms/order/OrderForm.tsx";
import {useAuthStore} from "../../store/auth.store.ts";
import {hasPermission} from "../../components/order/orderStatusUpdatePayload.ts";

export const CreateOrderPage = () => {

    const navigate = useNavigate();
    const permissions = useAuthStore((state) => state.me?.active_business?.permissions);
    const canCreateOrders = hasPermission(permissions, "orders.create");

    const createOrder =
        useCreateOrder();

    const handleCancel = () => {
        navigate("/orders");
    };


    const handleSubmit = async (
        values: OrderFormInput,
    ) => {

            console.log(values);

        try {

            await createOrder.mutateAsync(
                values,
            );

            navigate("/orders");

        } catch (error) {

            console.error(error);

        }

    };

    return (

        <Container
            maxWidth="xl"
            sx={{
                py: 4,
            }}
        >
            {!canCreateOrders ? (
                <Alert severity="error">
                    برای ثبت سفارش مجوز orders.create لازم است.
                </Alert>
            ) : <Box
                sx={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 4,
                }}
            >

                <OrderForm
                    mode="create"
                    loading={createOrder.isPending}
                    onSubmit={handleSubmit}
                    onCancel={handleCancel}
                />

            </Box>}

        </Container>

    );

};