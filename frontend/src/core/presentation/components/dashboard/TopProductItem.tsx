import {
    Box,
    LinearProgress,
    Stack,
    Typography,
} from "@mui/material";

interface Props {
    name: string;
    orderCount: number;
    percentage: number;
    revenue: number;
}

export const TopProductItem = ({
                                   name,
                                   orderCount,
                                   percentage,
                                   revenue,
                               }: Props) => {
    return (
        <Stack spacing={1.5}>
            <Stack
                direction="row"
                justifyContent="space-between"
                alignItems="center"
            >
                <Box>
                    <Typography
                        fontWeight={600}
                    >
                        {name}
                    </Typography>

                    <Typography
                        variant="caption"
                        color="text.secondary"
                    >
                        {orderCount} سفارش
                    </Typography>
                </Box>

                <Typography
                    variant="body2"
                    fontWeight={700}
                    color="success.main"
                >
                    {revenue.toLocaleString()} تومان
                </Typography>
            </Stack>

            <LinearProgress
                variant="determinate"
                value={percentage}
                sx={{
                    height: 8,
                    borderRadius: 999,
                }}
            />

            <Typography
                variant="caption"
                color="text.secondary"
            >
                {percentage}% از فروش
            </Typography>
        </Stack>
    );
};