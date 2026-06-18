import {
    Box,
    Typography,
} from "@mui/material";

import CheckCircleRoundedIcon
    from "@mui/icons-material/CheckCircleRounded";

export const AuthHero = () => {
    return (
        <Box
            sx={{
                maxWidth: 560,
            }}
        >
            <Typography
                sx={{
                    color: "#10281A",
                    fontWeight: 800,
                    fontSize: 18,
                    mb: 3,
                }}
            >
                EatHub
            </Typography>

            <Typography
                sx={{
                    fontSize: {
                        md: 52,
                    },

                    lineHeight: 1.2,

                    fontWeight: 800,

                    color: "#111827",
                }}
            >
                مدیریت هوشمند
                <br />
                رستوران و کافه
            </Typography>

            <Typography
                sx={{
                    mt: 3,

                    fontSize: 18,

                    lineHeight: 2,

                    color: "#6B7280",
                }}
            >
                فروش، انبار، سفارشات و گزارشات را
                در یک پلتفرم یکپارچه مدیریت کنید.
            </Typography>

            <Box
                sx={{
                    mt: 5,

                    display: "flex",

                    flexDirection: "column",

                    gap: 2,
                }}
            >
                <Feature
                    text="مدیریت فروش و صندوق"
                />

                <Feature
                    text="کنترل موجودی انبار"
                />

                <Feature
                    text="گزارشات مالی و تحلیلی"
                />

                <Feature
                    text="مدیریت سفارشات و مشتریان"
                />
            </Box>
        </Box>
    );
};

interface FeatureProps {
    text: string;
}

const Feature = ({
                     text,
                 }: FeatureProps) => (
    <Box
        sx={{
            display: "flex",
            alignItems: "center",
            gap: 1.5,
        }}
    >
        <CheckCircleRoundedIcon
            sx={{
                color: "#16A34A",
            }}
        />

        <Typography
            sx={{
                color: "#374151",
                fontWeight: 500,
            }}
        >
            {text}
        </Typography>
    </Box>
);