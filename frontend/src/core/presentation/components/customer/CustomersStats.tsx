import {
    AccountBalanceWalletOutlined,
    GroupsOutlined,
    ShoppingBagOutlined,
    TrendingUpOutlined,
} from "@mui/icons-material";
import {Grid, Paper, Stack, Typography} from "@mui/material";
import {formatCurrency} from "../../utils/formatCurrency.ts";


interface CustomersStatsProps {
    totalCustomers: number;

    totalBalance: number;

    totalOrders: number;

    totalSpent: number;
}

export function CustomersStats({
                                   totalCustomers,
                                   totalBalance,
                                   totalOrders,
                                   totalSpent,
                               }: CustomersStatsProps) {
    const items = [
        {
            title: "مشتریان",
            value: totalCustomers.toLocaleString(),
            icon: <GroupsOutlined color="primary"/>,
        },
        {
            title: "اعتبار حساب‌ها",
            value: formatCurrency(totalBalance),
            icon: <AccountBalanceWalletOutlined color="success"/>,
        },
        {
            title: "کل سفارش‌ها",
            value: totalOrders.toLocaleString(),
            icon: <ShoppingBagOutlined color="warning"/>,
        },
        {
            title: "مجموع خرید",
            value: formatCurrency(totalSpent),
            icon: <TrendingUpOutlined color="error"/>,
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
                        md: 3,
                    }}
                >
                    <Paper
                        elevation={0}
                        sx={{
                            p: 2.5,
                            border: 1,
                            borderColor: "divider",
                            borderRadius: 3,
                            height: "100%",
                        }}
                    >
                        <Stack
                            sx={{
                                flexDirection: "row",
                                justifyContent: "space-between",
                                alignItems: "center",
                            }}
                        >
                            <Stack
                                sx={{
                                    gap: 0.5,
                                }}
                            >
                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                >
                                    {item.title}
                                </Typography>

                                <Typography
                                    variant="h5"
                                    sx={{
                                        fontWeight: 700,
                                    }}
                                >
                                    {item.value}
                                </Typography>
                            </Stack>

                            {item.icon}
                        </Stack>
                    </Paper>
                </Grid>
            ))}
        </Grid>
    );
}