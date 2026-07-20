import {
    ArrowDownward,
    ArrowUpward,
} from "@mui/icons-material";
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
import {
    type CustomerTransaction,
    CustomerTransactionType
} from "../../../domain/entities/product/customer/CustomerTransaction.ts";
import {formatCurrency} from "../../utils/formatCurrency.ts";
import {formatDateTime} from "../../utils/formatDateTime.ts";



interface CustomerTransactionsTabProps {
    transactions: CustomerTransaction[];

    loading?: boolean;

    onOrderClick?(orderId: string): void;
}

export function CustomerTransactionsTab({
    transactions,
    loading = false,
    onOrderClick,
}: CustomerTransactionsTabProps) {

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
                    در حال دریافت تراکنش‌ها...
                </Typography>
            </Paper>
        );
    }

    if (transactions.length === 0) {
        return (
            <Paper
                variant="outlined"
                sx={{
                    p: 5,
                    textAlign: "center",
                }}
            >
                <Typography color="text.secondary">
                    تراکنشی ثبت نشده است.
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
                        <TableCell>نوع</TableCell>
                        <TableCell align="center">
                            مبلغ
                        </TableCell>
                        <TableCell align="center">
                            سفارش
                        </TableCell>
                        <TableCell>
                            توضیحات
                        </TableCell>
                        <TableCell align="center">
                            تاریخ
                        </TableCell>
                    </TableRow>
                </TableHead>

                <TableBody>
                    {transactions.map((transaction) => {

                        const isDeposit =
                            transaction.type === CustomerTransactionType.DEBIT;

                        return (
                            <TableRow
                                key={transaction.id}
                                hover
                            >
                                <TableCell>
                                    <Chip
                                        size="small"
                                        color={isDeposit ? "success" : "error"}
                                        icon={
                                            isDeposit
                                                ? <ArrowDownward fontSize="small"/>
                                                : <ArrowUpward fontSize="small"/>
                                        }
                                        label={
                                            isDeposit
                                                ? "شارژ حساب"
                                                : "برداشت"
                                        }
                                    />
                                </TableCell>

                                <TableCell
                                    align="center"
                                    sx={{
                                        color: isDeposit
                                            ? "success.main"
                                            : "error.main",
                                        fontWeight: 700,
                                    }}
                                >
                                    {isDeposit ? "+" : "-"}
                                    {formatCurrency(transaction.amount)}
                                </TableCell>

                                <TableCell align="center">
                                    {transaction.orderId ? (
                                        <Typography
                                            component="span"
                                            sx={{
                                                cursor: "pointer",
                                                color: "primary.main",
                                                fontWeight: 600,
                                            }}
                                            onClick={() =>
                                                onOrderClick?.(
                                                    transaction.orderId!,
                                                )
                                            }
                                        >
                                            #{transaction.orderId}
                                        </Typography>
                                    ) : (
                                        "-"
                                    )}
                                </TableCell>

                                <TableCell>
                                    {transaction.description || "-"}
                                </TableCell>

                                <TableCell align="center">
                                    {formatDateTime(
                                        transaction.createdAt,
                                    )}
                                </TableCell>
                            </TableRow>
                        );
                    })}
                </TableBody>
            </Table>
        </TableContainer>
    );
}