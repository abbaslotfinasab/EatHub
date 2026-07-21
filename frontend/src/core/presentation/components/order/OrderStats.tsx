import {
    Grid,
} from "@mui/material";

import ReceiptLongRoundedIcon from "@mui/icons-material/ReceiptLongRounded";
import ScheduleRoundedIcon from "@mui/icons-material/ScheduleRounded";
import SoupKitchenRoundedIcon from "@mui/icons-material/SoupKitchenRounded";
import CheckCircleRoundedIcon from "@mui/icons-material/CheckCircleRounded";

import { StatCard } from "../common/StatCard";

interface OrdersStatsProps {
    totalOrders: number;
    pendingOrders: number;
    preparingOrders: number;
    readyOrders: number;
}

export const OrdersStats = ({
    totalOrders,
    pendingOrders,
    preparingOrders,
    readyOrders,
}: OrdersStatsProps) => {

    const stats = [
        {
            title: "کل سفارشات",
            value: totalOrders.toLocaleString(),
            subtitle: "تمام سفارش‌ها",
            icon: <ReceiptLongRoundedIcon />,
            color: "#2563EB",
        },
        {
            title: "در انتظار",
            value: pendingOrders.toLocaleString(),
            subtitle: "منتظر تأیید",
            icon: <ScheduleRoundedIcon />,
            color: "#F59E0B",
        },
        {
            title: "در حال آماده‌سازی",
            value: preparingOrders.toLocaleString(),
            subtitle: "داخل آشپزخانه",
            icon: <SoupKitchenRoundedIcon />,
            color: "#8B5CF6",
        },
        {
            title: "آماده تحویل",
            value: readyOrders.toLocaleString(),
            subtitle: "منتظر تحویل",
            icon: <CheckCircleRoundedIcon />,
            color: "#16A34A",
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
};