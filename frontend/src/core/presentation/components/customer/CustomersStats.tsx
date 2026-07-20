import {
    AccountBalanceWalletOutlined,
    GroupsOutlined,
    ShoppingBagOutlined,
    TrendingUpOutlined,
    SouthWestRounded,
    NorthEastRounded,
} from "@mui/icons-material";
import {Grid, Paper, Stack, Typography} from "@mui/material";
import {formatCurrency} from "../../utils/formatCurrency.ts";

interface CustomersStatsProps {
    totalCustomers: number;

    creditors: number;

    debtors: number;

    totalOrders: number;

    totalSpent: number;
}

export function CustomersStats({
                                   totalCustomers,
                                   creditors,
                                   debtors,
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
            title: "بستانکاران",
            value: formatCurrency(creditors),
            icon: <NorthEastRounded color="success"/>,
        },
        {
            title: "بدهکاران",
            value: formatCurrency(debtors),
            icon: <SouthWestRounded color="error"/>,
        },
        {
            title: "کل سفارش‌ها",
            value: totalOrders.toLocaleString(),
            icon: <ShoppingBagOutlined color="warning"/>,
        },
        {
            title: "مجموع خرید",
            value: formatCurrency(totalSpent),
            icon: <TrendingUpOutlined color="primary"/>,
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
                        md: 2.4,
                    }}
                >
                    <Paper
                        elevation={0}
                        sx={{
                            p: 2.5,
                            border: 1,
                            borderColor: "divider",
                            borderRadius: 1,
                            height: "100%",
                            transition: "0.2s",

                            "&:hover": {
                                borderColor: "primary.main",
                                transform: "translateY(-2px)",
                            },
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
                            <AccountBalanceWalletOutlined
                                sx={{display: "none"}}
                            />

                            {item.icon}
                        </Stack>
                    </Paper>
                </Grid>
            ))}
        </Grid>
    );
}