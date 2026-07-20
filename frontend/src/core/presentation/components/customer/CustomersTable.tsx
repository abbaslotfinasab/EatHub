import {
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Typography,
} from "@mui/material";

import {CustomerTableRow} from "./CustomerTableRow";
import type {CustomerListItem} from "../../../domain/entities/product/customer/CustomerListItem";

interface CustomersTableProps {
    customers: CustomerListItem[];

    onView(customer: CustomerListItem): void;

    onEdit(customer: CustomerListItem): void;

    onRecharge(customer: CustomerListItem): void;

    onDelete(customer: CustomerListItem): void;
}

export function CustomersTable({
                                   customers,
                                   onView,
                                   onEdit,
                                   onRecharge,
                                   onDelete,
                               }: CustomersTableProps) {
    return (
        <TableContainer
            component={Paper}
            elevation={0}
            sx={{
                border: 1,
                borderColor: "divider",
                borderRadius: 3,
                overflow: "hidden",
            }}
        >
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell width={280}>
                            <Typography
                                sx={{
                                    fontWeight: 700,
                                }}
                            >
                                مشتری
                            </Typography>
                        </TableCell>

                        <TableCell width={170}>
                            <Typography
                                sx={{
                                    fontWeight: 700,
                                }}
                            >
                                موبایل
                            </Typography>
                        </TableCell>

                        <TableCell
                            align="center"
                            width={150}
                        >
                            <Typography
                                sx={{
                                    fontWeight: 700,
                                }}
                            >
                                مانده حساب
                            </Typography>
                        </TableCell>

                        <TableCell
                            align="center"
                            width={120}
                        >
                            <Typography
                                sx={{
                                    fontWeight: 700,
                                }}
                            >
                                سفارش‌ها
                            </Typography>
                        </TableCell>

                        <TableCell
                            align="center"
                            width={180}
                        >
                            <Typography
                                sx={{
                                    fontWeight: 700,
                                }}
                            >
                                مجموع خرید
                            </Typography>
                        </TableCell>

                        <TableCell
                            align="center"
                            width={170}
                        >
                            <Typography
                                sx={{
                                    fontWeight: 700,
                                }}
                            >
                                تاریخ عضویت
                            </Typography>
                        </TableCell>

                        <TableCell
                            align="right"
                            width={70}
                        >
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
                    {customers.length === 0 ? (
                        <TableRow>
                            <TableCell
                                colSpan={7}
                                align="center"
                                sx={{
                                    py: 10,
                                }}
                            >
                                <Typography
                                    variant="subtitle1"
                                    color="text.secondary"
                                >
                                    مشتری‌ای یافت نشد.
                                </Typography>
                            </TableCell>
                        </TableRow>
                    ) : (
                        customers.map((customer) => (
                            <CustomerTableRow
                                key={customer.id}
                                customer={customer}
                                onView={onView}
                                onEdit={onEdit}
                                onRecharge={onRecharge}
                                onDelete={onDelete}
                            />
                        ))
                    )}
                </TableBody>
            </Table>
        </TableContainer>
    );
}