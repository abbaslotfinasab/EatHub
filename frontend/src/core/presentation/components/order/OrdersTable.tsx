import {
    Paper,
    Table,
    TableBody,
    TableContainer,
    TableHead,
    TableRow,
    TableCell,
    Typography,
} from "@mui/material";

import {OrderTableRow} from "./OrderTableRow";
import type {OrderWithItems} from "../../../domain/entities/product/order/OrderWithItems.ts";

interface OrdersTableProps {
    orders: OrderWithItems[];

    onOrderClick?: (order: OrderWithItems) => void;

    onOrderMenuClick?: (
        event: React.MouseEvent<HTMLElement>,
        order: OrderWithItems,
    ) => void;
}

export const OrdersTable = ({
                                orders,
                                onOrderClick,
                                onOrderMenuClick,
                            }: OrdersTableProps) => {
    return (

        <TableContainer
            component={Paper}
            elevation={0}
            sx={{
                border: 1,
                borderColor: "divider",
                borderRadius: 3,
                overflow: "hidden",
                overflowX: "auto",
                overflowY: "hidden",
            }}
        >
            <Table>

                <TableHead>
                    <TableRow>

                        <TableCell>
                            <Typography
                                sx={{
                                    fontWeight: 700,
                                }}
                            >
                                شماره
                            </Typography>
                        </TableCell>

                        <TableCell><Typography
                            sx={{
                                fontWeight: 700,
                            }}
                        >
                            مشتری
                        </Typography></TableCell>

                        <TableCell><Typography
                            sx={{
                                fontWeight: 700,
                            }}
                        >
                            نوع سفارش
                        </Typography>
                        </TableCell>

                        <TableCell><Typography
                            sx={{
                                fontWeight: 700,
                            }}
                        >
                            میز
                        </Typography></TableCell>

                        <TableCell>
                            <Typography
                                sx={{
                                    fontWeight: 700,
                                }}
                            >
                                توضیحات
                            </Typography></TableCell>

                        <TableCell><Typography
                            sx={{
                                fontWeight: 700,
                            }}
                        >
                            مبلغ
                        </Typography></TableCell>

                        <TableCell>
                            <Typography
                                sx={{
                                    fontWeight: 700,
                                }}
                            >
                                وضعیت سفارش
                            </Typography>
                        </TableCell>

                        {/*<TableCell>وضعیت پرداخت</TableCell>*/}

                        {/*<TableCell>روش پرداخت</TableCell>*/}

                        <TableCell align="center">
                            <Typography
                                sx={{
                                    fontWeight: 700,
                                }}
                            >
                                زمان
                            </Typography>
                        </TableCell>

                        <TableCell>
                            <Typography
                                sx={{
                                    fontWeight: 700,
                                }}
                            >
                                عملیات
                            </Typography>
                        </TableCell>

                    </TableRow>
                </TableHead>

                <TableBody>

                    {orders.map((order) => (
                        <OrderTableRow
                            key={order.order.id}
                            order={order}
                            onClick={onOrderClick}
                            onMenuClick={onOrderMenuClick}
                        />
                    ))}

                </TableBody>

            </Table>
        </TableContainer>
    );
};