import {
    Box,
    Paper,
    Stack,
    Typography,
    Chip,
} from "@mui/material";

import TrendingUpRoundedIcon from "@mui/icons-material/TrendingUpRounded";
import TrendingDownRoundedIcon from "@mui/icons-material/TrendingDownRounded";

interface Props {
    title: string;
    value: string;
    subtitle?: string;
    growth?: number;
    icon: React.ReactNode;
    color: string;
}

export const StatCard = ({
                             title,
                             value,
                             subtitle,
                             growth,
                             icon,
                             color,
                         }: Props) => {
    const isPositive = (growth ?? 0) >= 0;

    return (
        <Paper
            elevation={0}
            sx={{
                p: 3,
                height: "100%",
                borderRadius: 4,
                border: "1px solid",
                borderColor: "divider",
                transition: ".2s",

                "&:hover": {
                    transform: "translateY(-3px)",
                    boxShadow:
                        "0 12px 24px rgba(0,0,0,.06)",
                },
            }}
        >
            <Stack
                direction="row"
                justifyContent="space-between"
                alignItems="flex-start"
            >
                <Box>
                    <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                            fontSize: 15,
                            fontWeight: 700,
                            color: "text.secondary",
                        }}
                    >
                        {title}
                    </Typography>

                    <Typography
                        variant="h4"
                        sx={{
                            fontSize: 20,
                            fontWeight: 500,
                        }}

                        mt={1}
                    >
                        {value}
                    </Typography>

                    {subtitle && (
                        <Typography
                            variant="caption"
                            color="text.secondary"
                        >
                            {subtitle}
                        </Typography>
                    )}
                </Box>

                <Box
                    sx={{
                        width: 52,
                        height: 52,
                        borderRadius: 3,
                        bgcolor: `${color}15`,
                        color,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                    }}
                >
                    {icon}
                </Box>
            </Stack>

            {growth !== undefined && (
                <Box mt={3}>
                    <Chip
                        size="small"
                        icon={
                            isPositive ? (
                                <TrendingUpRoundedIcon />
                            ) : (
                                <TrendingDownRoundedIcon />
                            )
                        }
                        label={`${Math.abs(growth)}%`}
                        color={
                            isPositive
                                ? "success"
                                : "error"
                        }
                    />
                </Box>
            )}
        </Paper>
    );
};