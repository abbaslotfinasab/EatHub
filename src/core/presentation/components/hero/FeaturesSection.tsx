// src/features/landing/components/FeaturesSection/FeaturesSection.tsx

import {
    Box,
    Container,
    Typography,
} from "@mui/material";

import Grid from "@mui/material/Grid";

import ShoppingBagRoundedIcon
    from "@mui/icons-material/ShoppingBagRounded";

import Inventory2RoundedIcon
    from "@mui/icons-material/Inventory2Rounded";

import PointOfSaleRoundedIcon
    from "@mui/icons-material/PointOfSaleRounded";

import EventSeatRoundedIcon
    from "@mui/icons-material/EventSeatRounded";

import InsightsRoundedIcon
    from "@mui/icons-material/InsightsRounded";

import GroupsRoundedIcon
    from "@mui/icons-material/GroupsRounded";

import { FeatureCard } from "./FeatureCard";

export const FeaturesSection = () => {
    const features = [
        {
            title: "سفارش‌گیری سریع",
            description:
                "ثبت سفارش حضوری، بیرون‌بر و آنلاین در چند ثانیه.",
            icon: <ShoppingBagRoundedIcon />,
        },

        {
            title: "مدیریت انبار",
            description:
                "کنترل موجودی مواد اولیه و هشدار کمبود موجودی.",
            icon: <Inventory2RoundedIcon />,
        },

        {
            title: "صندوق فروش",
            description:
                "مدیریت پرداخت‌ها و صدور فاکتور.",
            icon: <PointOfSaleRoundedIcon />,
        },

        {
            title: "مدیریت میزها",
            description:
                "نمایش وضعیت میزها و رزروها.",
            icon: <EventSeatRoundedIcon />,
        },

        {
            title: "گزارش‌ها",
            description:
                "تحلیل فروش و عملکرد کسب‌وکار.",
            icon: <InsightsRoundedIcon />,
        },

        {
            title: "مدیریت کارکنان",
            description:
                "کنترل شیفت‌ها و عملکرد پرسنل.",
            icon: <GroupsRoundedIcon />,
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
                    امکانات
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
                    همه چیز برای مدیریت رستوران،
                    <br />
                    در یک پلتفرم واحد
                </Typography>
            </Box>

            <Grid container spacing={3}>
                {features.map((feature) => (
                    <Grid
                        key={feature.title}
                        size={{
                            xs: 12,
                            md: 6,
                            lg: 4,
                        }}
                    >
                        <FeatureCard {...feature} />
                    </Grid>
                ))}
            </Grid>
        </Container>
    );
};