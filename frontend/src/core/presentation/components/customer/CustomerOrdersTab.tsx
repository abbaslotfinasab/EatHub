import {
    Chip,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Typography,
} from "@mui/material";
import type { Order } from "../../../domain/entities/product/order/Order";
import {OrderStatusChip} from "../order/OrderStatusChip.tsx";
import {formatCurrency} from "../../utils/formatCurrency.ts";
import {formatDateTime} from "../../utils/formatDateTime.ts";

interface CustomerOrdersTabProps {
    orders: Order[];

    loading?: boolean;

    onOrderClick?(order: Order): void;
}

export function CustomerOrdersTab({
    orders,
    loading = false,
    onOrderClick,
}: CustomerOrdersTabProps) {

    if (loading) {
        return (
            <Paper
                variant="outlined"
                sx={{
                    p: 5,
                    textAlign: "center",
                }}
            >
                <Typography color="text.secondary">
                    در حال دریافت سفارش‌ها...
                </Typography>
            </Paper>
        );
    }

    if (orders.length === 0) {
        return (
            <Paper
                variant="outlined"
                sx={{
                    p: 5,
                    textAlign: "center",
                }}
            >
                <Typography color="text.secondary">
                    این مشتری هنوز سفارشی ثبت نکرده است.
                </Typography>
            </Paper>
        );
    }

    return (
        <TableContainer
            component={Paper}
            variant="outlined"
        >
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell>شماره</TableCell>
                        <TableCell align="center">نوع</TableCell>
                        <TableCell align="center">وضعیت</TableCell>
                        <TableCell align="center">مبلغ</TableCell>
                        <TableCell align="center">تاریخ</TableCell>
                    </TableRow>
                </TableHead>

                <TableBody>
                    {orders.map((order) => (
                        <TableRow
                            key={order.id}
                            hover
                            sx={{
                                cursor: "pointer",
                            }}
                            onClick={() => onOrderClick?.(order)}
                        >
                            <TableCell>
                                #{order.id}
                            </TableCell>

                            <TableCell align="center">
                                <Chip
                                    size="small"
                                    label={order.status}
                                />
                            </TableCell>

                            <TableCell align="center">
                                <OrderStatusChip
                                    status={order.status}
                                />
                            </TableCell>

                            <TableCell align="center">
                                {formatCurrency(order.totalAmount)}
                            </TableCell>

                            <TableCell align="center">
                                {formatDateTime(order.createdAt)}
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
}