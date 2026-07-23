import {Grid} from "@mui/material";

import SellRoundedIcon from "@mui/icons-material/SellRounded";
import ReceiptLongRoundedIcon from "@mui/icons-material/ReceiptLongRounded";
import EventSeatRoundedIcon from "@mui/icons-material/EventSeatRounded";
import WarningAmberRoundedIcon from "@mui/icons-material/WarningAmberRounded";

import {StatCard} from "../common/StatCard";
import {formatCurrency} from "../../utils/formatCurrency";

interface DashboardStatsProps {
    todaySales: number;
    todayOrders: number;
    activeOrders: number;
    todayReservations: number;
    inventoryAlerts: number;
}

export function DashboardStats({
                                   todaySales,
                                   todayOrders,
                                   todayReservations,
                                   inventoryAlerts,
                               }: DashboardStatsProps) {

    const stats = [
        {
            title: "فروش امروز",
            value: formatCurrency(todaySales),
            subtitle: "فروش ثبت شده",
            icon: <SellRoundedIcon/>,
            color: "#16A34A",
        },
        {
            title: "سفارشات امروز",
            value: todayOrders.toLocaleString(),
            subtitle: "سفارشات تکمیل شده",
            icon: <ReceiptLongRoundedIcon/>,
            color: "#2563EB",
        },
        {
            title: "رزروهای امروز",
            value: todayReservations.toLocaleString(),
            subtitle: "رزرو ثبت شده",
            icon: <EventSeatRoundedIcon/>,
            color: "#9333EA",
        },
        {
            title: "هشدارهای انبار",
            value: inventoryAlerts.toLocaleString(),
            subtitle: "نیاز به تأمین",
            icon: <WarningAmberRoundedIcon/>,
            color: "#EA580C",
        },
    ];

    return (
        <Grid
            container
            spacing={2.5}
        >
            {stats.map((item) => (
                <Grid
                    key={item.title}
                    size={{
                        xs: 12,
                        sm: 6,
                        lg: 3,
                    }}
                >
                    <StatCard
                        title={item.title}
                        value={item.value}
                        subtitle={item.subtitle}
                        icon={item.icon}
                        color={item.color}
                    />
                </Grid>
            ))}
        </Grid>
    );
}