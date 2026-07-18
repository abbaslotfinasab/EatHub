import {
    Paper,
    Table,
    TableBody,
    TableContainer,
    TableHead,
    TableRow,
    TableCell, alpha,
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
                borderRadius: 3,
                border: "1px solid",
                borderColor: "divider",
                overflow: "hidden",
            }}
        >
            <Table
                sx={{
                    "& .MuiTableCell-head": {
                        backgroundColor: alpha("#10281A", 0.05),
                        color: "text.secondary",
                        fontWeight: 700,
                        fontSize: 13,
                        whiteSpace: "nowrap",
                    },
                }}
            >

                <TableHead>
                    <TableRow>

                        <TableCell>شماره</TableCell>

                        <TableCell>مشتری</TableCell>

                        <TableCell>نوع سفارش</TableCell>

                        <TableCell>میز</TableCell>

                        <TableCell>توضیحات</TableCell>

                        <TableCell>مبلغ</TableCell>

                        <TableCell>وضعیت</TableCell>

                        <TableCell>زمان</TableCell>

                        <TableCell align="right">
                            عملیات
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