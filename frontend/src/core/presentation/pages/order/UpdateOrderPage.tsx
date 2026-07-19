// presentation/pages/order/UpdateOrderPage.tsx

import {useMemo} from "react";
import {useNavigate, useParams} from "react-router-dom";

import {
    Box,
    CircularProgress,
    Container,
    Stack,
    Typography,
} from "@mui/material";


import {useGetOrderById} from "../../hooks/order/useGetOrderById.ts";
import {useUpdateOrder} from "../../hooks/order/useUpdateOrder";


import type {OrderFormInput} from "../../forms/order/OrderFormInput";
import {OrderFormMapper} from "../../forms/order/OrderFormMapper.tsx";
import {OrderForm} from "../../forms/order/OrderForm.tsx";

export const UpdateOrderPage = () => {

    const navigate = useNavigate();

    const {id = ""} = useParams();

    // ============================
    // Queries
    // ============================

    const {
        data: order,
        isLoading,
    } = useGetOrderById(id);

    // ============================
    // Mutation
    // ============================

    const updateOrder =
        useUpdateOrder();

    // ============================
    // Initial Values
    // ============================

    const initialValues = useMemo(() => {

        if (!order) {
            return undefined;
        }

        return OrderFormMapper.toForm(
            order,
        );

    }, [order]);

    // ============================
    // Submit
    // ============================

    const handleSubmit = async (
        values: OrderFormInput,
    ) => {

        try {

            await updateOrder.mutateAsync({
                id: id,
                input: values,
            });

            navigate("/orders");

        } catch (error) {

            console.error(error);

        }

    };

    // ============================
    // Loading
    // ============================

    if (isLoading) {

        return (

            <Stack
                sx={{
                    height: "70vh",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 2,
                }}
            >

                <CircularProgress/>

                <Typography>

                    در حال دریافت سفارش...

                </Typography>

            </Stack>

        );

    }

    // ============================
    // Not Found
    // ============================

    if (!order || !initialValues) {

        return (

            <Stack
                sx={{
                    height: "60vh",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 2,
                }}
            >

                <Typography variant="h5">

                    سفارش پیدا نشد

                </Typography>

            </Stack>

        );

    }

    // ============================
    // Render
    // ============================

    return (

        <Container
            maxWidth="xl"
            sx={{
                py: 4,
            }}
        >

            <Box
                sx={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 4,
                }}
            >

                <OrderForm
                    mode="edit"
                    loading={updateOrder.isPending}
                    onSubmit={handleSubmit}
                />

            </Box>

        </Container>

    );

};