// src/features/landing/components/HeroSection/DashboardPreview/PreviewChart.tsx

import {
    Box,
    Paper,
    Typography,
} from "@mui/material";

import {
    ResponsiveContainer,
    LineChart,
    Line,
    XAxis,
    Tooltip,
} from "recharts";

const data = [
    {
        day: "ش",
        sales: 8,
    },
    {
        day: "ی",
        sales: 12,
    },
    {
        day: "د",
        sales: 10,
    },
    {
        day: "س",
        sales: 18,
    },
    {
        day: "چ",
        sales: 16,
    },
    {
        day: "پ",
        sales: 24,
    },
    {
        day: "ج",
        sales: 20,
    },
];

export const PreviewChart = () => {
    return (
        <Paper
            elevation={0}
            sx={{
                p: 4,

                borderRadius: 5,

                border: "1px solid #F1F5F9",
            }}
        >
            {/* Header */}

            <Box
                sx={{
                    mb: 4,
                }}
            >
                <Typography
                    sx={{
                        fontWeight: 700,

                        fontSize: 18,
                    }}
                >
                    درآمد هفتگی
                </Typography>

                <Typography
                    sx={{
                        mt: 1,

                        color: "#64748B",

                        fontSize: 14,
                    }}
                >
                    روند فروش ۷ روز گذشته
                </Typography>
            </Box>

            {/* Chart */}

            <Box
                sx={{
                    height: 300,
                }}
            >
                <ResponsiveContainer
                    width="100%"
                    height="100%"
                >
                    <LineChart data={data}>
                        <XAxis
                            dataKey="day"
                            axisLine={false}
                            tickLine={false}
                        />

                        <Tooltip />

                        <Line
                            type="monotone"
                            dataKey="sales"
                            stroke="#10281A"
                            strokeWidth={4}
                            dot={false}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </Box>
        </Paper>
    );
};