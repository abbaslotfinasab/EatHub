// src/features/landing/components/HeroSection/DashboardPreview/PreviewStats.tsx

import Grid from "@mui/material/Grid";

import SellRoundedIcon
    from "@mui/icons-material/SellRounded";

import ReceiptLongRoundedIcon
    from "@mui/icons-material/ReceiptLongRounded";

import EventSeatRoundedIcon
    from "@mui/icons-material/EventSeatRounded";

import WarningAmberRoundedIcon
    from "@mui/icons-material/WarningAmberRounded";

import { PreviewStatCard } from "./PreviewStatCard";

export const PreviewStats = () => {
    const stats = [
        {
            title: "فروش امروز",
            value: "12,000,000",

            growth: "+12%",

            icon: <SellRoundedIcon />,

            color: "#16A34A",
        },

        {
            title: "سفارشات فعال",
            value: "34",

            growth: "+8%",

            icon: <ReceiptLongRoundedIcon />,

            color: "#2563EB",
        },

        {
            title: "رزروهای امروز",
            value: "12",

            growth: "+4%",

            icon: <EventSeatRoundedIcon />,

            color: "#9333EA",
        },

        {
            title: "هشدارهای انبار",
            value: "5",

            growth: "-2%",

            icon: <WarningAmberRoundedIcon />,

            color: "#EA580C",
        },
    ];

    return (
        <Grid container spacing={3}>
            {stats.map((item) => (
                <Grid
                    key={item.title}
                    size={{
                        xs: 12,
                        sm: 6,
                        lg: 3,
                    }}
                >
                    <PreviewStatCard {...item} />
                </Grid>
            ))}
        </Grid>
    );
};