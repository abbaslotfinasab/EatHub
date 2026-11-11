import {Alert, Box, Card, CardContent, Chip, CircularProgress, Divider, Stack, Typography} from "@mui/material";

import type {OrderStatusType} from "../../../domain/entities/product/order/Order.ts";
import {useGetOrderStatusHistory} from "../../hooks/order/useGetOrderStatusHistory.ts";
import {orderStatusLabels} from "../../utils/orderStatusLabels.ts";

interface Props {
    orderId: string;
    enabled?: boolean;
}

function formatDate(value: string): string {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return new Intl.DateTimeFormat("fa-IR", {
        dateStyle: "medium",
        timeStyle: "short",
    }).format(date);
}

function statusLabel(status: OrderStatusType | null): string {
    return status ? orderStatusLabels[status] : "ثبت اولیه سفارش";
}

export function OrderStatusHistoryPanel({orderId, enabled = true}: Props) {
    const query = useGetOrderStatusHistory(orderId, enabled);

    return (
        <Card elevation={0} sx={{mt: 2, border: 1, borderColor: "divider", borderRadius: 2}}>
            <CardContent>
                <Stack spacing={2}>
                    <Box>
                        <Typography variant="h6" sx={{fontWeight: 700}}>
                            تاریخچه وضعیت سفارش
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            تمام تغییرات ثبت‌شده به همراه زمان و عامل تغییر
                        </Typography>
                    </Box>

                    <Divider />

                    {query.isLoading && (
                        <Stack direction="row" spacing={1} alignItems="center">
                            <CircularProgress size={20} />
                            <Typography variant="body2">در حال دریافت تاریخچه...</Typography>
                        </Stack>
                    )}

                    {query.isError && (
                        <Alert severity="error">
                            دریافت تاریخچه وضعیت سفارش ناموفق بود. لطفاً دوباره تلاش کنید.
                        </Alert>
                    )}

                    {query.isSuccess && query.data.history.length === 0 && (
                        <Alert severity="info">
                            برای این سفارش هنوز رویداد تاریخچه‌ای ثبت نشده است.
                        </Alert>
                    )}

                    {query.data?.history.map((entry, index) => (
                        <Stack key={entry.id} direction="row" spacing={1.5} alignItems="stretch">
                            <Stack alignItems="center" sx={{width: 18, flexShrink: 0}}>
                                <Box sx={{
                                    width: 10,
                                    height: 10,
                                    mt: 0.8,
                                    borderRadius: "50%",
                                    bgcolor: index === 0 ? "success.main" : "primary.main",
                                }} />
                                {index < query.data.history.length - 1 && (
                                    <Box sx={{width: 2, flex: 1, minHeight: 28, bgcolor: "divider"}} />
                                )}
                            </Stack>

                            <Stack spacing={0.75} sx={{pb: 1.5, flex: 1, minWidth: 0}}>
                                <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                                    <Typography sx={{fontWeight: 700}}>
                                        {entry.fromStatus
                                            ? `${statusLabel(entry.fromStatus)} ← ${statusLabel(entry.toStatus)}`
                                            : statusLabel(entry.toStatus)}
                                    </Typography>
                                    <Chip
                                        size="small"
                                        variant="outlined"
                                        label={entry.toStatus ? orderStatusLabels[entry.toStatus] : "ثبت"}
                                    />
                                </Stack>
                                <Typography variant="caption" color="text.secondary">
                                    {formatDate(entry.createdAt)}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    عامل تغییر: {entry.actor?.name ?? "کاربر ثبت‌نشده / سیستم"}
                                </Typography>
                            </Stack>
                        </Stack>
                    ))}
                </Stack>
            </CardContent>
        </Card>
    );
}
