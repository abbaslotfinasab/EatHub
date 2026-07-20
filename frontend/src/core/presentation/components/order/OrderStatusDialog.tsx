import {
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    MenuItem,
    Stack,
    TextField,
    Button,
    Paper, Typography,
} from "@mui/material";


import {LoadingButton} from "@mui/lab";

import ReceiptLongRoundedIcon from "@mui/icons-material/ReceiptLong";
import PaidRoundedIcon from "@mui/icons-material/Paid";
import PaymentsRoundedIcon from "@mui/icons-material/Payments";


import {useState} from "react";

import type {
    Order,
    OrderStatusType,
    PaymentMethodType,
    PaymentStatusType,
} from "../../../domain/entities/product/order/Order";


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


    const [status, setStatus] =
        useState<OrderStatusType>(
            order?.status ?? "pending",
        );


    const [paymentStatus, setPaymentStatus] =
        useState<PaymentStatusType>(
            order?.paymentStatus ?? "pending",
        );


    const [paymentMethod, setPaymentMethod] =
        useState<PaymentMethodType>(
            order?.paymentMethod ?? "cash",
        );


    if (!order) {
        return null;
    }


    const handleSubmit = () => {

        onSubmit({

            status,

            paymentStatus,

            paymentMethod,

        });

    };


    return (

        <Dialog
            open={open}
            onClose={onClose}
            fullWidth
            maxWidth="sm"
        >

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

                            <TextField
                                fullWidth
                                select
                                value={status}
                                onChange={(e) =>
                                    setStatus(
                                        e.target.value as OrderStatusType
                                    )
                                }
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

                            <TextField
                                fullWidth
                                select
                                value={paymentStatus}
                                onChange={(e) =>
                                    setPaymentStatus(
                                        e.target.value as PaymentStatusType
                                    )
                                }
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

                            <TextField
                                fullWidth
                                select
                                value={paymentMethod}
                                onChange={(e) =>
                                    setPaymentMethod(
                                        e.target.value as PaymentMethodType
                                    )
                                }
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
                    loading={loading}
                    variant="contained"
                    size="large"
                    sx={{
                        minWidth: 180,
                    }}
                    onClick={handleSubmit}
                >
                    ذخیره تغییرات
                </LoadingButton>

            </DialogActions>


        </Dialog>

    );

}