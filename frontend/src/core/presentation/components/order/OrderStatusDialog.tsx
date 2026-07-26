import {useEffect} from "react";

import {
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    MenuItem,
    Paper,
    Stack,
    TextField,
    Typography,
} from "@mui/material";

import {LoadingButton} from "@mui/lab";

import ReceiptLongRoundedIcon from "@mui/icons-material/ReceiptLong";
import PaidRoundedIcon from "@mui/icons-material/Paid";
import PaymentsRoundedIcon from "@mui/icons-material/Payments";

import {Controller, useForm} from "react-hook-form";
import {zodResolver} from "@hookform/resolvers/zod";

import type {
    Order,
    OrderStatusType,
    PaymentMethodType,
    PaymentStatusType,
} from "../../../domain/entities/product/order/Order";

import {
    OrderStatusFormSchema,
    type OrderStatusFormInput,
} from "../../forms/order/order-status/OrderStatusFormInput";

interface Props {
    open: boolean;

    order?: Order | null;

    loading?: boolean;

    onClose(): void;

    onSubmit(data: {
        status: OrderStatusType;
        paymentStatus: PaymentStatusType;
        paymentMethod: PaymentMethodType;
    }): void;
}

export function OrderStatusDialog({
                                      open,
                                      order,
                                      loading = false,
                                      onClose,
                                      onSubmit,
                                  }: Props) {
    const {
        control,
        handleSubmit,
        reset,
    } = useForm<OrderStatusFormInput>({
        resolver: zodResolver(OrderStatusFormSchema),

        defaultValues: {
            status: "pending",
            paymentStatus: "pending",
            paymentMethod: "cash",
        },
    });

    useEffect(() => {
        if (!open || !order) {
            return;
        }

        reset({
            status: order.status,
            paymentStatus: order.paymentStatus ?? "pending",
            paymentMethod: order.paymentMethod ?? "cash",
        });
    }, [open, order, reset]);

    if (!order) {
        return null;
    }

    return (
        <Dialog
            open={open}
            onClose={onClose}
            fullWidth
            maxWidth="sm"
        >
            <form onSubmit={handleSubmit(onSubmit)}>

                <DialogTitle>
                    تغییر وضعیت سفارش
                </DialogTitle>

                <DialogContent>

                    <Stack
                        sx={{
                            gap: 3,
                            mt: 1,
                        }}
                    >

                        {/* وضعیت سفارش */}

                        <Paper
                            variant="outlined"
                            sx={{
                                p: 3,
                                borderRadius: 3,
                            }}
                        >

                            <Stack spacing={2}>

                                <Stack
                                    sx={{
                                        flexDirection: "row",
                                        gap: 1,
                                        alignItems: "center",
                                    }}
                                >

                                    <ReceiptLongRoundedIcon
                                        color="primary"
                                    />

                                    <Typography
                                        sx={{
                                            fontWeight: 700,
                                        }}
                                    >
                                        وضعیت سفارش
                                    </Typography>
                                </Stack>

                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                >
                                    مرحله فعلی سفارش را انتخاب کنید.
                                </Typography>

                                <Controller
                                    control={control}
                                    name="status"
                                    render={({field}) => (

                                        <TextField
                                            {...field}
                                            fullWidth
                                            select
                                        >

                                            <MenuItem value="pending">
                                                در انتظار
                                            </MenuItem>

                                            <MenuItem value="confirmed">
                                                تایید شده
                                            </MenuItem>

                                            <MenuItem value="preparing">
                                                در حال آماده سازی
                                            </MenuItem>

                                            <MenuItem value="ready">
                                                آماده تحویل
                                            </MenuItem>

                                            <MenuItem value="completed">
                                                تکمیل شده
                                            </MenuItem>

                                            <MenuItem value="cancelled">
                                                لغو شده
                                            </MenuItem>

                                        </TextField>

                                    )}
                                />

                            </Stack>

                        </Paper>

                        {/* وضعیت پرداخت */}

                        <Paper
                            variant="outlined"
                            sx={{
                                p: 3,
                                borderRadius: 3,
                            }}
                        >

                            <Stack spacing={2}>

                                <Stack
                                    sx={{
                                        flexDirection: "row",
                                        gap: 1,
                                        alignItems: "center",
                                    }}
                                >

                                    <PaidRoundedIcon
                                        color="success"
                                    />

                                    <Typography
                                        sx={{
                                            fontWeight: 700,
                                        }}
                                    >
                                        وضعیت پرداخت
                                    </Typography>

                                </Stack>

                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                >
                                    مشخص کنید پرداخت انجام شده است یا خیر.
                                </Typography>

                                <Controller
                                    control={control}
                                    name="paymentStatus"
                                    render={({field}) => (

                                        <TextField
                                            {...field}
                                            fullWidth
                                            select
                                        >

                                            <MenuItem value="pending">
                                                در انتظار
                                            </MenuItem>

                                            <MenuItem value="unpaid">
                                                پرداخت نشده
                                            </MenuItem>

                                            <MenuItem value="paid">
                                                پرداخت شده
                                            </MenuItem>

                                            <MenuItem value="failed">
                                                ناموفق
                                            </MenuItem>

                                            <MenuItem value="refunded">
                                                برگشت داده شده
                                            </MenuItem>

                                        </TextField>

                                    )}
                                />

                            </Stack>

                        </Paper>

                        {/* روش پرداخت */}

                        <Paper
                            variant="outlined"
                            sx={{
                                p: 3,
                                borderRadius: 3,
                            }}
                        >

                            <Stack spacing={2}>

                                <Stack
                                    sx={{
                                        flexDirection: "row",
                                        gap: 1,
                                        alignItems: "center",
                                    }}
                                >

                                    <PaymentsRoundedIcon
                                        sx={{
                                            color: "warning.main",
                                        }}
                                    />

                                    <Typography
                                        sx={{
                                            fontWeight: 700,
                                        }}
                                    >
                                        روش پرداخت
                                    </Typography>

                                </Stack>

                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                >
                                    روش تسویه سفارش را انتخاب کنید.
                                </Typography>

                                <Controller
                                    control={control}
                                    name="paymentMethod"
                                    render={({field}) => (

                                        <TextField
                                            {...field}
                                            fullWidth
                                            select
                                        >

                                            <MenuItem value="cash">
                                                نقدی
                                            </MenuItem>

                                            <MenuItem value="card">
                                                کارت
                                            </MenuItem>

                                            <MenuItem value="customer_account">
                                                حساب مشتری
                                            </MenuItem>

                                        </TextField>

                                    )}
                                />

                            </Stack>

                        </Paper>

                    </Stack>

                </DialogContent>

                <DialogActions
                    sx={{
                        px: 3,
                        pb: 3,
                        pt: 2,
                    }}
                >

                    <Button
                        onClick={onClose}
                        size="large"
                    >
                        انصراف
                    </Button>

                    <LoadingButton
                        type="submit"
                        loading={loading}
                        variant="contained"
                        size="large"
                        sx={{
                            minWidth: 180,
                        }}
                    >
                        ذخیره تغییرات
                    </LoadingButton>

                </DialogActions>

            </form>
        </Dialog>
    );
}