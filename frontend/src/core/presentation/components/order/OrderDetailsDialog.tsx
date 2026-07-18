import CloseRoundedIcon from "@mui/icons-material/CloseRounded";
import PersonRoundedIcon from "@mui/icons-material/PersonRounded";
import RestaurantRoundedIcon from "@mui/icons-material/RestaurantRounded";
import AccessTimeRoundedIcon from "@mui/icons-material/AccessTimeRounded";
import LocalDiningRoundedIcon from "@mui/icons-material/LocalDiningRounded";

import {
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Divider,
    Grid,
    IconButton,
    MenuItem,
    Paper,
    Stack,
    Table,
    TableBody,
    TableCell, TableContainer,
    TableHead,
    TableRow,
    TextField,
    Typography,
} from "@mui/material";



import { OrderStatusChip } from "./OrderStatusChip";
import type { OrderWithItems } from "../../../domain/entities/product/order/OrderWithItems";
import {OrderStatus, type OrderStatusType} from "../../../domain/entities/product/order/Order.ts";

interface OrderDetailsDialogProps {
    open: boolean;
    order?: OrderWithItems;
    loading?: boolean;

    onClose: () => void;

    onStatusChange?: (
        status: OrderStatusType,
    ) => void;

    onPrint?: () => void;
}

const ORDER_STATUS_OPTIONS = [
    {
        value: OrderStatus.PENDING,
        label: "در انتظار",
    },
    {
        value: OrderStatus.CONFIRMED,
        label: "تأیید شده",
    },
    {
        value: OrderStatus.PREPARING,
        label: "درحال آماده سازی",
    },
    {
        value: OrderStatus.READY,
        label: "آماده تحویل",
    },
    {
        value: OrderStatus.COMPLETED,
        label: "تحویل شده",
    },
    {
        value: OrderStatus.CANCELLED,
        label: "لغو شده",
    },
];

export const OrderDetailsDialog = ({
    open,
    order,
    loading = false,
    onClose,
    onStatusChange,
}: OrderDetailsDialogProps) => {

    if (!order) {
        return null;
    }

    const data = order.order;

    return (
        <Dialog
            open={open}
            onClose={onClose}
            fullWidth
            maxWidth="lg"
        >

            <DialogTitle
                sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    py: 2,
                }}
            >

                <Stack spacing={1}>

                    <Typography
                        variant="h6"
                        fontWeight={700}
                    >
                        سفارش #{data.id}
                    </Typography>

                    <OrderStatusChip
                        status={data.status}
                    />

                </Stack>

                <IconButton
                    onClick={onClose}
                >
                    <CloseRoundedIcon />
                </IconButton>

            </DialogTitle>

            <Divider />

            <DialogContent>

                <Grid
                    container
                    spacing={2}
                >

                    {/* Customer */}

                    <Grid size={{xs:12, md:6}}>

                        <Paper
                            variant="outlined"
                            sx={{
                                p:3,
                                height:"100%",
                            }}
                        >

                            <Stack spacing={2}>

                                <Stack
                                    direction="row"
                                    spacing={1}
                                    alignItems="center"
                                >

                                    <PersonRoundedIcon />

                                    <Typography
                                        fontWeight={700}
                                    >
                                        اطلاعات مشتری
                                    </Typography>

                                </Stack>

                                <Divider/>

                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                >
                                    نام مشتری
                                </Typography>

                                <Typography
                                    fontWeight={600}
                                >
                                    {data.customerName}
                                </Typography>

                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                >
                                    شماره تماس
                                </Typography>

                                <Typography>
                                    {data.customerPhone ?? "-"}
                                </Typography>

                            </Stack>

                        </Paper>

                    </Grid>

                    {/* Order Info */}

                    <Grid size={{xs:12, md:6}}>

                        <Paper
                            variant="outlined"
                            sx={{
                                p:3,
                                height:"100%",
                            }}
                        >

                            <Stack spacing={2}>

                                <Stack
                                    direction="row"
                                    spacing={1}
                                    alignItems="center"
                                >

                                    <RestaurantRoundedIcon />

                                    <Typography
                                        fontWeight={700}
                                    >
                                        اطلاعات سفارش
                                    </Typography>

                                </Stack>

                                <Divider/>

                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                >
                                    نوع سفارش
                                </Typography>

                                <Typography>

                                    {data.orderType === "dine_in"
                                        ? "حضوری"
                                        : data.orderType === "delivery"
                                            ? "ارسال"
                                            : "بیرون بر"}

                                </Typography>

                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                >
                                    میز
                                </Typography>

                                <Typography>
                                    {data.tableId ?? "-"}
                                </Typography>

                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                >
                                    زمان ثبت
                                </Typography>

                                <Stack
                                    direction="row"
                                    spacing={1}
                                    alignItems="center"
                                >

                                    <AccessTimeRoundedIcon
                                        fontSize="small"
                                    />

                                    <Typography>
                                        {data.createdAt ?? "-"}
                                    </Typography>

                                </Stack>

                                <TextField
                                    select
                                    fullWidth
                                    size="small"
                                    label="وضعیت سفارش"
                                    value={data.status}
                                    onChange={(e)=>
                                        onStatusChange?.(
                                            e.target.value as OrderStatusType
                                        )
                                    }
                                >

                                    {ORDER_STATUS_OPTIONS.map((item)=>(
                                        <MenuItem
                                            key={item.value}
                                            value={item.value}
                                        >
                                            {item.label}
                                        </MenuItem>
                                    ))}

                                </TextField>

                            </Stack>

                        </Paper>

                    </Grid>
                            {/* ==========================
                        Order Items
                    =========================== */}

                    <Grid size={{ xs: 12 }}>
                        <Paper
                            variant="outlined"
                            sx={{
                                p: 3,
                            }}
                        >
                            <Stack spacing={2}>

                                <Stack
                                    direction="row"
                                    spacing={1}
                                    alignItems="center"
                                >
                                    <LocalDiningRoundedIcon />

                                    <Typography
                                        fontWeight={700}
                                    >
                                        اقلام سفارش
                                    </Typography>
                                </Stack>

                                <Divider />

                                <TableContainer>

                                    <Table size="small">

                                        <TableHead>

                                            <TableRow>

                                                <TableCell>
                                                    آیتم
                                                </TableCell>

                                                <TableCell align="center">
                                                    تعداد
                                                </TableCell>

                                                <TableCell align="right">
                                                    قیمت واحد
                                                </TableCell>

                                                <TableCell align="right">
                                                    مبلغ
                                                </TableCell>

                                            </TableRow>

                                        </TableHead>

                                        <TableBody>

                                            {order.orderItems.map((item) => (

                                                <TableRow
                                                    key={item.id}
                                                    hover
                                                >

                                                    <TableCell>

                                                        <Stack spacing={0.5}>

                                                            <Typography
                                                                fontWeight={600}
                                                            >
                                                                {item.menuItemName}
                                                            </Typography>

                                                            {item.notes && (

                                                                <Typography
                                                                    variant="caption"
                                                                    color="text.secondary"
                                                                >
                                                                    {item.notes}
                                                                </Typography>

                                                            )}

                                                        </Stack>

                                                    </TableCell>

                                                    <TableCell align="center">
                                                        {item.quantity}
                                                    </TableCell>

                                                    <TableCell align="right">
                                                        {(item.unitPrice ?? 0).toLocaleString()}
                                                    </TableCell>

                                                    <TableCell align="right">
                                                        {(item.totalPrice ?? 0).toLocaleString()}
                                                    </TableCell>

                                                </TableRow>

                                            ))}

                                        </TableBody>

                                    </Table>

                                </TableContainer>

                            </Stack>
                        </Paper>
                    </Grid>

                    {/* ==========================
                        Notes
                    =========================== */}

                    <Grid size={{ xs: 12, md: 6 }}>

                        <Paper
                            variant="outlined"
                            sx={{
                                p: 3,
                                height: "100%",
                            }}
                        >

                            <Stack spacing={2}>

                                <Typography
                                    fontWeight={700}
                                >
                                    توضیحات سفارش
                                </Typography>

                                <Divider />

                                <Typography
                                    color="text.secondary"
                                >
                                    {data.notes || "توضیحی ثبت نشده است."}
                                </Typography>

                            </Stack>

                        </Paper>

                    </Grid>

                    {/* ==========================
                        Summary
                    =========================== */}

                    <Grid size={{ xs: 12, md: 6 }}>

                        <Paper
                            variant="outlined"
                            sx={{
                                p: 3,
                                height: "100%",
                            }}
                        >

                            <Stack spacing={2}>

                                <Typography
                                    fontWeight={700}
                                >
                                    خلاصه مالی
                                </Typography>

                                <Divider />

                                <Stack
                                    direction="row"
                                    justifyContent="space-between"
                                >
                                    <Typography color="text.secondary">
                                        جمع اقلام
                                    </Typography>

                                    <Typography fontWeight={600}>
                                        {data.subtotal.toLocaleString()} تومان
                                    </Typography>
                                </Stack>

                                <Stack
                                    direction="row"
                                    justifyContent="space-between"
                                >
                                    <Typography color="text.secondary">
                                        تخفیف
                                    </Typography>

                                    <Typography
                                        color="success.main"
                                        fontWeight={600}
                                    >
                                        {data.discount.toLocaleString()} تومان
                                    </Typography>
                                </Stack>

                                <Stack
                                    direction="row"
                                    justifyContent="space-between"
                                >
                                    <Typography color="text.secondary">
                                        مالیات
                                    </Typography>

                                    <Typography fontWeight={600}>
                                        {data.tax.toLocaleString()} تومان
                                    </Typography>
                                </Stack>

                                <Divider />

                                <Stack
                                    direction="row"
                                    justifyContent="space-between"
                                >
                                    <Typography
                                        variant="h6"
                                        fontWeight={700}
                                    >
                                        مبلغ نهایی
                                    </Typography>

                                    <Typography
                                        variant="h6"
                                        color="primary.main"
                                        fontWeight={700}
                                    >
                                        {data.totalAmount.toLocaleString()} تومان
                                    </Typography>
                                </Stack>

                            </Stack>

                        </Paper>

                    </Grid>

                        </Grid>

            </DialogContent>

            <Divider />

            <DialogActions
                sx={{
                    px: 3,
                    py: 2,
                    justifyContent: "space-between",
                }}
            >

                <Button
                    variant="outlined"
                    onClick={print}
                >
                    چاپ فاکتور
                </Button>

                <Stack
                    direction="row"
                    spacing={1}
                >

                    <Button
                        color="inherit"
                        onClick={onClose}
                    >
                        بستن
                    </Button>

                </Stack>

            </DialogActions>

        </Dialog>
    );
};