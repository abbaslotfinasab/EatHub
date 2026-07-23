import {
    Card,
    CardContent,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Typography,
    Paper,
} from "@mui/material";

import type {OrderWithItems} from "../../../domain/entities/product/order/OrderWithItems";
import {OrderTableRow} from "../order/OrderTableRow.tsx";


interface Props {
    orders: OrderWithItems[];

    onOrderClick?: (order: OrderWithItems) => void;

    onOrderMenuClick?: (
        event: React.MouseEvent<HTMLElement>,
        order: OrderWithItems,
    ) => void;
}

export function OrdersTable({
                                orders,
                                onOrderClick,
                                onOrderMenuClick,
                            }: Props) {

    return (
        <Card
            elevation={0}
            sx={{
                borderRadius: 4,
                border: 1,
                borderColor: "divider",
            }}
        >
            <CardContent>

                <Typography
                    variant="h6"
                    sx={{
                        fontWeight: 700,
                        mb: 2,
                    }}
                >
                    سفارشات امروز
                </Typography>

                <TableContainer
                    component={Paper}
                    elevation={0}
                >
                    <Table>

                        <TableHead>
                            <TableRow>

                                <TableCell>شماره</TableCell>

                                <TableCell>مشتری</TableCell>

                                <TableCell>نوع</TableCell>

                                <TableCell>میز</TableCell>

                                <TableCell>توضیحات</TableCell>

                                <TableCell>مبلغ</TableCell>

                                <TableCell>وضعیت</TableCell>

                                <TableCell align="center">
                                    زمان
                                </TableCell>

                                <TableCell>
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

            </CardContent>
        </Card>
    );
}