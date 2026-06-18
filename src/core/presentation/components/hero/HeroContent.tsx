// src/features/landing/components/HeroSection/HeroContent.tsx

import {
    Box,
    Chip,
    Typography,
} from "@mui/material";

import BoltRoundedIcon
    from "@mui/icons-material/BoltRounded";

import { HeroButtons } from "./HeroButtons";

export const HeroContent = () => {
    return (
        <Box
            sx={{
                textAlign: "center",

                maxWidth: 900,

                mx: "auto",

                mb: {
                    xs: 8,
                    md: 12,
                },
            }}
        >
            {/* Badge */}

            <Chip
                icon={<BoltRoundedIcon />}
                label="پلتفرم مدیریت رستوران و کافه"
                sx={{
                    mb: 4,

                    bgcolor: "#EEF7F1",

                    color: "#10281A",

                    fontWeight: 700,

                    px: 1,

                    height: 40,

                    borderRadius: 100,
                }}
            />

            {/* Title */}

            <Typography
                component="h1"
                sx={{
                    fontWeight: 800,

                    lineHeight: 1.2,

                    letterSpacing: "-0.03em",

                    mb: 3,

                    fontSize: {
                        xs: "2.5rem",
                        md: "4.5rem",
                    },
                }}
            >
                همه چیز برای مدیریت
                <br />
                رستوران شما، در یک پلتفرم
            </Typography>

            {/* Description */}

            <Typography
                sx={{
                    color: "#6B7280",

                    maxWidth: 700,

                    mx: "auto",

                    lineHeight: 2,

                    mb: 5,

                    fontSize: {
                        xs: "1rem",
                        md: "1.25rem",
                    },
                }}
            >
                سفارش‌گیری، صندوق فروش، مدیریت انبار،
                میزها، حسابداری و گزارش‌ها؛
                همه چیز در EatHub.
            </Typography>

            <HeroButtons />
        </Box>
    );
};