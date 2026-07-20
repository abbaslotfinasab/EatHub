import {
    AccountBalanceWalletOutlined,
    CalendarTodayOutlined,
    LocalMallOutlined,
    PhoneOutlined,
    ShoppingBagOutlined,
    PersonOutlined,
} from "@mui/icons-material";
import {
    Grid,
    Paper,
    Stack,
    Typography,
} from "@mui/material";
import type {CustomerListItem} from "../../../domain/entities/product/customer/CustomerListItem";
import {formatCurrency} from "../../utils/formatCurrency.ts";
import {formatDate} from "../../utils/formatDate.ts";


interface CustomerOverviewProps {
    customer: CustomerListItem;
}

export function CustomerOverview({
                                     customer,
                                 }: CustomerOverviewProps) {
    const items = [
        {
            title: "نام مشتری",
            value: customer.name,
            icon: <PersonOutlined color="primary"/>,
        },
        {
            title: "شماره موبایل",
            value: customer.phone,
            icon: <PhoneOutlined color="primary"/>,
        },
        {
            title: "مانده حساب",
            value: formatCurrency(customer.balance ?? 0),
            icon: <AccountBalanceWalletOutlined color="success"/>,
            color:
                (customer.balance ?? 0) > 0
                    ? "success.main"
                    : (customer.balance ?? 0) < 0
                        ? "error.main"
                        : "text.primary",
        },
        {
            title: "تعداد سفارش",
            value: `${customer.totalOrders ?? 0}`,
            icon: <ShoppingBagOutlined color="warning"/>,
        },
        {
            title: "مجموع خرید",
            value: formatCurrency(customer.totalSpent ?? 0),
            icon: <LocalMallOutlined color="error"/>,
        },
        {
            title: "تاریخ عضویت",
            value: customer.createdAt
                ? formatDate(customer.createdAt)
                : "-",
            icon: <CalendarTodayOutlined color="action"/>,
        },
    ];

    return (
        <Grid
            container
            spacing={2}
        >
            {items.map((item) => (
                <Grid
                    key={item.title}
                    size={{
                        xs: 12,
                        sm: 6,
                    }}
                >
                    <Paper
                        variant="outlined"
                        sx={{
                            p: 2,
                            height: "100%",
                            borderRadius: 2,
                        }}
                    >
                        <Stack
                            sx={{
                                flexDirection: "row",
                                gap: 2,
                                alignItems: "center",
                            }}
                        >
                            {item.icon}

                            <Stack
                                sx={{
                                    gap: 0.5,
                                }}
                            >
                                <Typography
                                    variant="caption"
                                    color="text.secondary"
                                >
                                    {item.title}
                                </Typography>

                                <Typography
                                    variant="subtitle1"
                                    color={item.color}
                                    sx={{
                                        fontWeight: 700,
                                    }}
                                >
                                    {item.value}
                                </Typography>
                            </Stack>
                        </Stack>
                    </Paper>
                </Grid>
            ))}
        </Grid>
    );
}