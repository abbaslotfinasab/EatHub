import {
    AccountBalanceWalletOutlined,
    ShoppingCartOutlined,
    TuneOutlined,
} from "@mui/icons-material";
import {
    Timeline,
    TimelineConnector,
    TimelineContent,
    TimelineDot,
    TimelineItem,
    TimelineSeparator,
} from "@mui/lab";
import {Paper, Stack, Typography} from "@mui/material";
import {
    CustomerTransactionType,
    type CustomerTransaction
} from "../../../domain/entities/product/customer/CustomerTransaction";
import {formatCurrency} from "../../utils/formatCurrency.ts";
import {formatDateTime} from "../../utils/formatDateTime.ts";


interface CustomerTransactionTimelineProps {
    transactions: CustomerTransaction[];
}

export function CustomerTransactionTimeline({
                                                transactions,
                                            }: CustomerTransactionTimelineProps) {

    if (transactions.length === 0) {
        return (
            <Paper
                variant="outlined"
                sx={{
                    p: 4,
                    textAlign: "center",
                }}
            >
                <Typography color="text.secondary">
                    تراکنشی وجود ندارد.
                </Typography>
            </Paper>
        );
    }

    return (
        <Timeline
            sx={{
                p: 0,
                m: 0,
                "& .MuiTimelineItem-root:before": {
                    display: "none",
                },
            }}
        >
            {transactions.map((transaction, index) => {

                const config = getTransactionConfig(transaction);

                return (
                    <TimelineItem key={transaction.id}>
                        <TimelineSeparator>

                            <TimelineDot color={config.color}>
                                {config.icon}
                            </TimelineDot>

                            {index !== transactions.length - 1 && (
                                <TimelineConnector/>
                            )}

                        </TimelineSeparator>

                        <TimelineContent
                            sx={{
                                pb: 3,
                            }}
                        >
                            <Stack spacing={0.5}>

                                <Typography
                                    sx={{
                                        fontWeight: 700,
                                    }}
                                >
                                    {config.title}
                                </Typography>

                                <Typography
                                    color={config.textColor}
                                    sx={{
                                        fontWeight: 600,
                                    }}
                                >
                                    {config.prefix}
                                    {formatCurrency(transaction.amount)}
                                </Typography>

                                {transaction.description && (
                                    <Typography
                                        variant="body2"
                                        color="text.secondary"
                                    >
                                        {transaction.description}
                                    </Typography>
                                )}

                                <Typography
                                    variant="caption"
                                    color="text.disabled"
                                >
                                    {formatDateTime(transaction.createdAt)}
                                </Typography>

                            </Stack>
                        </TimelineContent>
                    </TimelineItem>
                );
            })}
        </Timeline>
    );
}

function getTransactionConfig(
    transaction: CustomerTransaction,
) {

    switch (transaction.type) {

        case CustomerTransactionType.CREDIT:
            return {
                title: "شارژ حساب",
                prefix: "+",
                color: "success" as const,
                textColor: "success.main",
                icon: <AccountBalanceWalletOutlined fontSize="small"/>,
            };

        case CustomerTransactionType.DEBIT:
            return {
                title: "پرداخت سفارش",
                prefix: "-",
                color: "error" as const,
                textColor: "error.main",
                icon: <ShoppingCartOutlined fontSize="small"/>,
            };

        case CustomerTransactionType.ADJUST:
        default:
            return {
                title: "اصلاح موجودی",
                prefix: "",
                color: "warning" as const,
                textColor: "warning.main",
                icon: <TuneOutlined fontSize="small"/>,
            };
    }
}