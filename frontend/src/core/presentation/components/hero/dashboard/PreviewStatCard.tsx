// src/features/landing/components/HeroSection/DashboardPreview/PreviewStatCard.tsx

import {
    Box,
    Paper,
    Typography,
} from "@mui/material";

interface Props {
    title: string;

    value: string;

    growth: string;

    icon: React.ReactNode;

    color: string;
}

export const PreviewStatCard = ({
                                    title,
                                    value,
                                    growth,
                                    icon,
                                    color,
                                }: Props) => {
    return (
        <Paper
            elevation={0}
            sx={{
                p: 3,

                borderRadius: 5,

                border: "1px solid #F1F5F9",

                bgcolor: "#FFF",

                transition: ".2s",

                "&:hover": {
                    transform: "translateY(-3px)",

                    boxShadow:
                        "0 20px 40px rgba(15,23,42,.08)",
                },
            }}
        >
            <Box
                sx={{
                    display: "flex",

                    justifyContent: "space-between",

                    alignItems: "center",
                }}
            >
                <Box>
                    <Typography
                        sx={{
                            color: "#64748B",

                            fontSize: 14,
                        }}
                    >
                        {title}
                    </Typography>

                    <Typography
                        sx={{
                            mt: 1,

                            fontWeight: 800,

                            fontSize: 28,

                            color: "#0F172A",
                        }}
                    >
                        {value}
                    </Typography>
                </Box>

                <Box
                    sx={{
                        width: 54,
                        height: 54,

                        borderRadius: 4,

                        bgcolor: `${color}15`,

                        color,

                        display: "flex",

                        alignItems: "center",

                        justifyContent: "center",
                    }}
                >
                    {icon}
                </Box>
            </Box>

            <Typography
                sx={{
                    mt: 3,

                    fontSize: 13,

                    fontWeight: 700,

                    color:
                        growth.startsWith("+")
                            ? "#16A34A"
                            : "#DC2626",
                }}
            >
                {growth} نسبت به دیروز
            </Typography>
        </Paper>
    );
};