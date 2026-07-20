import {
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    MenuItem,
    Stack,
    TextField,
    Button,
} from "@mui/material";

import {LoadingButton} from "@mui/lab";

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
                        flexDirection: "row",
                        alignItems: "center",
                        gap: 2,
                    }}
                >

                    <TextField
                        select
                        label="وضعیت سفارش"
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


                    <TextField
                        select
                        label="وضعیت پرداخت"
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


                    <TextField
                        select
                        label="روش پرداخت"
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


            </DialogContent>


            <DialogActions>

                <Button
                    onClick={onClose}
                >
                    انصراف
                </Button>


                <LoadingButton
                    loading={loading}
                    variant="contained"
                    onClick={handleSubmit}
                >

                    ذخیره

                </LoadingButton>


            </DialogActions>


        </Dialog>

    );

}