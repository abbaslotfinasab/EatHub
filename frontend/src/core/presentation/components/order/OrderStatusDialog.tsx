import {useEffect, useRef, useState} from "react";

import {
    Button,
    Alert,
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
import type {RefundOrderInput} from "../../../domain/entities/product/order/RefundOrderInput.ts";
import type {RefundOrderResult} from "../../../domain/entities/product/order/RefundOrderInput.ts";

import {
    OrderStatusFormSchema,
    type OrderStatusFormInput,
} from "../../forms/order/order-status/OrderStatusFormInput";

interface Props {
    open: boolean;

    order?: Order | null;

    loading?: boolean;

    refundLoading?: boolean;

    canManagePayments?: boolean;

    error?: string | null;

    refundError?: string | null;

    refundResult?: RefundOrderResult | null;

    refundRecoveryLoading?: boolean;

    refundRecoveryError?: string | null;

    onClose(): void;

    onSubmit(data: {
        status?: OrderStatusType;
        paymentStatus?: PaymentStatusType;
        paymentMethod?: PaymentMethodType;
    }): void;

    onRefund(data: Omit<RefundOrderInput, "orderId">): Promise<void>;
}

export function OrderStatusDialog({
                                      open,
                                      order,
                                      loading = false,
                                      refundLoading = false,
                                      canManagePayments = false,
                                      error = null,
                                      refundError = null,
                                      refundResult = null,
                                      refundRecoveryLoading = false,
                                      refundRecoveryError = null,
                                      onClose,
                                      onSubmit,
                                      onRefund,
                                  }: Props) {
    const [refundOpen, setRefundOpen] = useState(false);
    const [refundReason, setRefundReason] = useState("");
    const [refundReference, setRefundReference] = useState("");
    const refundAttempt = useRef<{intent: string; key: string} | null>(null);
    const {
        control,
        handleSubmit,
        reset,
        formState: {dirtyFields, isDirty},
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
        <>
        <Dialog
            open={open}
            onClose={onClose}
            fullWidth
            maxWidth="sm"
        >
            <form onSubmit={handleSubmit((data) => onSubmit({
                ...(dirtyFields.status ? {status: data.status} : {}),
                ...(canManagePayments && dirtyFields.paymentStatus
                    ? {paymentStatus: data.paymentStatus}
                    : {}),
                ...(canManagePayments && dirtyFields.paymentMethod
                    ? {paymentMethod: data.paymentMethod}
                    : {}),
            }))}>

                <DialogTitle>
                    تغییر وضعیت سفارش
                </DialogTitle>

                <DialogContent>

                    {refundRecoveryLoading && (
                        <Alert severity="info" sx={{mb: 2}}>
                            در حال بازیابی رسید بازپرداخت ثبت‌شده...
                        </Alert>
                    )}

                    {refundRecoveryError && (
                        <Alert severity="error" sx={{mb: 2}}>
                            بازیابی رسید بازپرداخت انجام نشد: {refundRecoveryError}
                        </Alert>
                    )}

                    {refundResult && (
                        <Alert severity="success" sx={{mb: 2}}>
                            بازپرداخت ثبت‌شده: {Number(refundResult.amount).toLocaleString()} —
                            شناسه {refundResult.id} — {new Date(refundResult.created_at).toLocaleString()}
                            {refundResult.reference ? ` — مرجع: ${refundResult.reference}` : ""}
                        </Alert>
                    )}

                    {error && (
                        <Alert severity="error" sx={{mb: 2}}>
                            {error}
                        </Alert>
                    )}

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

                        {canManagePayments && <>
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
                                    تکمیل سفارش به‌تنهایی پرداخت را تأیید نمی‌کند؛ فقط پس از دریافت وجه، وضعیت پرداخت را «پرداخت‌شده» انتخاب کنید.
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

                                            {order.paymentStatus === "refunded" && <MenuItem value="refunded" disabled>
                                                برگشت داده شده؛ فقط از سابقه بازپرداخت
                                            </MenuItem>}

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

                                <Typography variant="body2" color="text.secondary">
                                    برای سفارش دارای سابقه حساب مشتری، هنگام تغییر روش پرداخت، وضعیت اصلاح‌شده پرداخت را نیز انتخاب کنید.
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
                        </>}

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

                    {canManagePayments && order.paymentStatus === "paid" && (
                        <Button
                            color="warning"
                            onClick={() => setRefundOpen(true)}
                            disabled={loading || refundLoading}
                        >
                            ثبت بازپرداخت کامل
                        </Button>
                    )}

                    <LoadingButton
                        type="submit"
                        loading={loading}
                        disabled={!isDirty}
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

        <Dialog open={refundOpen} onClose={() => setRefundOpen(false)} fullWidth maxWidth="sm">
            <form onSubmit={async (event) => {
                event.preventDefault();
                if (order.paymentMethod !== "customer_account") {
                    return;
                }
                const reason = refundReason.trim();
                const reference = refundReference.trim();
                const intent = JSON.stringify([
                    order.id,
                    order.paymentMethod,
                    reason,
                    reference,
                ]);
                const key = refundAttempt.current?.intent === intent
                    ? refundAttempt.current.key
                    : crypto.randomUUID();
                refundAttempt.current = {intent, key};
                try {
                    await onRefund({
                        idempotencyKey: key,
                        reason,
                        reference,
                    });
                    if (refundAttempt.current?.key === key) {
                        refundAttempt.current = null;
                    }
                    setRefundOpen(false);
                    setRefundReason("");
                    setRefundReference("");
                } catch {
                    // The parent surfaces the backend validation message.
                }
            }}>
                <DialogTitle>ثبت بازپرداخت کامل</DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{mt: 1}}>
                        <Alert severity="warning">
                            لغو یا تکمیل سفارش به‌تنهایی بازپرداخت انجام نمی‌دهد. مبلغ کیف پول از سابقه تسویه محاسبه می‌شود.
                        </Alert>
                        {order.paymentMethod === "customer_account" ? (
                            <>
                                <TextField
                                    label="علت بازپرداخت"
                                    value={refundReason}
                                    onChange={(event) => setRefundReason(event.target.value)}
                                    required
                                    multiline
                                    minRows={2}
                                />
                                <TextField
                                    label="شماره مرجع (اختیاری)"
                                    value={refundReference}
                                    onChange={(event) => setRefundReference(event.target.value)}
                                />
                            </>
                        ) : (
                            <Alert severity="error">
                                ایت‌هاب سابقه تغییرناپذیر مبلغ پرداخت نقدی/کارتی ندارد؛ بنابراین بازپرداخت را نمی‌توان در برنامه نهایی یا به‌عنوان پرداخت تأییدشده ثبت کرد. بازپرداخت واقعی باید خارج از ایت‌هاب انجام و در سامانه مالی معتبر ثبت شود.
                            </Alert>
                        )}
                        {refundError && <Alert severity="error">{refundError}</Alert>}
                    </Stack>
                </DialogContent>
                <DialogActions sx={{px: 3, pb: 3}}>
                    <Button onClick={() => setRefundOpen(false)}>انصراف</Button>
                    <LoadingButton
                        type="submit"
                        loading={refundLoading}
                        disabled={!refundReason.trim() || order.paymentMethod !== "customer_account"}
                        color="warning"
                        variant="contained"
                    >
                        تأیید و ثبت بازپرداخت
                    </LoadingButton>
                </DialogActions>
            </form>
        </Dialog>
        </>
    );
}
