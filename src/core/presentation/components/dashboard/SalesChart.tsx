import {
    Paper,
    Stack,
    Typography,
    Box,
} from "@mui/material";

import {
    ResponsiveContainer,
    AreaChart,
    Area,
    XAxis,
    Tooltip,
    CartesianGrid,
} from "recharts";

interface Props {
    data: {
        date: string;
        sales: number;
    }[];
}

export const SalesChart = ({
                               data,
                           }: Props) => {
    return (
        <Paper
            elevation={0}
            sx={{
                p: 3,
                borderRadius: 4,
                border: "1px solid",
                borderColor: "divider",
            }}
        >
            <Stack spacing={3}>
                <Box>
                    <Typography
                        variant="h6"
                        fontWeight={700}
                    >
                        فروش ۷ روز اخیر
                    </Typography>

                    <Typography
                        variant="body2"
                        color="text.secondary"
                    >
                        روند فروش رستوران در هفته جاری
                    </Typography>
                </Box>

                <Box height={320}>
                    <ResponsiveContainer
                        width="100%"
                        height="100%"
                    >
                        <AreaChart data={data}>
                            <defs>
                                <linearGradient
                                    id="salesGradient"
                                    x1="0"
                                    y1="0"
                                    x2="0"
                                    y2="1"
                                >
                                    <stop
                                        offset="5%"
                                        stopColor="#10281A"
                                        stopOpacity={0.3}
                                    />

                                    <stop
                                        offset="95%"
                                        stopColor="#10281A"
                                        stopOpacity={0}
                                    />
                                </linearGradient>
                            </defs>

                            <CartesianGrid
                                strokeDasharray="3 3"
                                vertical={false}
                            />

                            <XAxis
                                dataKey="date"
                                tickLine={false}
                                axisLine={false}
                            />

                            <Tooltip />

                            <Area
                                type="monotone"
                                dataKey="sales"
                                stroke="#10281A"
                                strokeWidth={3}
                                fill="url(#salesGradient)"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </Box>
            </Stack>
        </Paper>
    );
};