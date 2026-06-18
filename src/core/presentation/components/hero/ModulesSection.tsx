// src/features/landing/components/ModulesSection/ModulesSection.tsx

import {
    Box,
    Container,
    Typography,
} from "@mui/material";

import Grid from "@mui/material/Grid";

import ReceiptLongRoundedIcon
    from "@mui/icons-material/ReceiptLongRounded";

import Inventory2RoundedIcon
    from "@mui/icons-material/Inventory2Rounded";

import GroupsRoundedIcon
    from "@mui/icons-material/GroupsRounded";

import EventSeatRoundedIcon
    from "@mui/icons-material/EventSeatRounded";

import AnalyticsRoundedIcon
    from "@mui/icons-material/AnalyticsRounded";

import PointOfSaleRoundedIcon
    from "@mui/icons-material/PointOfSaleRounded";

import { ModuleCard } from "./ModuleCard";

export const ModulesSection = () => {
    const modules = [
        {
            title: "مدیریت سفارشات",
            description:
                "ثبت سفارش، صدور فاکتور و پیگیری وضعیت سفارش‌ها.",
            icon: <ReceiptLongRoundedIcon />,
        },

        {
            title: "مدیریت انبار",
            description:
                "کنترل مواد اولیه و هشدار کاهش موجودی.",
            icon: <Inventory2RoundedIcon />,
        },

        {
            title: "مدیریت کارکنان",
            description:
                "برنامه شیفت و مدیریت عملکرد پرسنل.",
            icon: <GroupsRoundedIcon />,
        },

        {
            title: "رزرو میزها",
            description:
                "مدیریت رزروها و وضعیت میزهای رستوران.",
            icon: <EventSeatRoundedIcon />,
        },

        {
            title: "گزارش‌ها",
            description:
                "تحلیل فروش و عملکرد کسب‌وکار.",
            icon: <AnalyticsRoundedIcon />,
        },

        {
            title: "صندوق فروش",
            description:
                "مدیریت پرداخت‌ها و تراکنش‌ها.",
            icon: <PointOfSaleRoundedIcon />,
        },
    ];

    return (
        <Container
            maxWidth="lg"
            sx={{
                py: 14,
            }}
        >
            <Box
                sx={{
                    textAlign: "center",
                    mb: 8,
                }}
            >
                <Typography
                    sx={{
                        color: "#10281A",
                        fontWeight: 700,
                        mb: 2,
                    }}
                >
                    ماژول‌ها
                </Typography>

                <Typography
                    sx={{
                        fontSize: {
                            xs: "2rem",
                            md: "3rem",
                        },

                        fontWeight: 800,

                        lineHeight: 1.3,
                    }}
                >
                    هر چیزی که رستوران شما
                    <br />
                    برای رشد نیاز دارد
                </Typography>
            </Box>

            <Grid container spacing={3}>
                {modules.map((module) => (
                    <Grid
                        key={module.title}
                        size={{
                            xs: 12,
                            md: 6,
                            lg: 4,
                        }}
                    >
                        <ModuleCard {...module} />
                    </Grid>
                ))}
            </Grid>
        </Container>
    );
};