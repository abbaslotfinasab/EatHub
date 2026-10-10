import {
    Paper,
    Stack,
    Typography,
    Box,
    ToggleButton,
    ToggleButtonGroup,
} from "@mui/material";

import {
    ResponsiveContainer,
    AreaChart,
    Area,
    XAxis,
    Tooltip,
    CartesianGrid,
} from "recharts";
import {formatChartDate} from "../../utils/formatChartDate.ts";
import {formatTooltipDate} from "../../utils/formatTooltipDate.ts";

interface Props {
    data: {
        date: string;
        sales: number;
    }[];
    period: "weekly" | "monthly";
    onPeriodChange: (period: "weekly" | "monthly") => void;
}

export const SalesChart = ({
                               data,
                               period,
                               onPeriodChange,
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
                <Stack
                    direction={{xs: "column", sm: "row"}}
                    spacing={2}
                    sx={{
                        alignItems: {xs: "stretch", sm: "center"},
                        justifyContent: "space-between",
                    }}
                >
                    <Box>
                        <Typography
                            variant="h6"
                            sx={{fontWeight: 700}}
                        >
                            {period === "weekly" ? "فروش ۷ روز اخیر" : "فروش ماه جاری"}
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            {period === "weekly"
                                ? "روند فروش رستوران در هفته جاری"
                                : "فروش روزانه از ابتدای ماه تا امروز"}
                        </Typography>
                    </Box>

                    <ToggleButtonGroup
                        exclusive
                        size="small"
                        value={period}
                        onChange={(_event, value: "weekly" | "monthly" | null) => {
                            if (value) onPeriodChange(value);
                        }}
                        aria-label="بازه نمودار فروش"
                        sx={{alignSelf: {xs: "flex-start", sm: "auto"}}}
                    >
                        <ToggleButton value="weekly" aria-label="هفتگی">
                            هفتگی
                        </ToggleButton>
                        <ToggleButton value="monthly" aria-label="ماهانه">
                            ماهانه
                        </ToggleButton>
                    </ToggleButtonGroup>
                </Stack>

                <Box sx={{height: 320}}>
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
                                tickFormatter={formatChartDate}
                                tickLine={false}
                                axisLine={false}
                            />

                            <Tooltip
                                labelFormatter={formatTooltipDate}
                            />
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
