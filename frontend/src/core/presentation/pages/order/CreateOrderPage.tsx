import {useNavigate} from "react-router-dom";
import {useRef} from "react";

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

    const createOrder = useCreateOrder();
    const pendingIdempotency = useRef<{ fingerprint: string; key: string } | null>(null);
    const storageKey = "eathub.order.create.pending.v1";

    const handleCancel = () => {
        navigate("/orders");
    };


    const handleSubmit = async (
        values: OrderFormInput,
    ) => {
        const fingerprint = JSON.stringify({
            businessId: useAuthStore.getState().me?.active_business?.id ?? null,
            values,
        });
        let pending = pendingIdempotency.current;

        try {
            const stored = sessionStorage.getItem(storageKey);
            if (stored) {
                const parsed = JSON.parse(stored) as { fingerprint?: string; key?: string };
                if (parsed.fingerprint === fingerprint && typeof parsed.key === "string") {
                    pending = { fingerprint, key: parsed.key };
                }
            }
        } catch {
            // Keep the in-memory retry key when session storage is unavailable.
        }

        if (!pending || pending.fingerprint !== fingerprint) {
            pending = { fingerprint, key: crypto.randomUUID() };
        }
        pendingIdempotency.current = pending;

        try {
            sessionStorage.setItem(storageKey, JSON.stringify(pending));
        } catch {
            // The in-memory key still protects retries during this page session.
        }

        try {
            await createOrder.mutateAsync({ input: values, idempotencyKey: pending.key });
            pendingIdempotency.current = null;
            try {
                sessionStorage.removeItem(storageKey);
            } catch {
                // Navigation after a successful response remains safe.
            }
            navigate("/orders");
        } catch (error) {
            // Preserve the key: a retry must represent the exact same create intent.
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