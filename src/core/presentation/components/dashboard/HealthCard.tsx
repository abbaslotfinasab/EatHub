import {
    Paper,
    Stack,
    Typography,
    Box,
    Chip,
} from "@mui/material";

interface Props {
    title: string;
    status: "success" | "warning" | "error";
    primaryValue: string;
    secondaryValue: string;
}

const statusConfig = {
    success: {
        color: "#22C55E",
        label: "سالم",
    },
    warning: {
        color: "#F59E0B",
        label: "نیاز به بررسی",
    },
    error: {
        color: "#EF4444",
        label: "بحرانی",
    },
};

export const HealthCard = ({
                               title,
                               status,
                               primaryValue,
                               secondaryValue,
                           }: Props) => {
    const config = statusConfig[status];

    return (
        <Paper
            elevation={0}
            sx={{
                p: 3,
                borderRadius: 4,
                border: "1px solid",
                borderColor: "divider",
                height: "100%",
            }}
        >
            <Stack spacing={2}>
                <Stack
                    direction="row"
                    justifyContent="space-between"
                    alignItems="center"
                >
                    <Typography
                        variant="h6"
                        fontWeight={700}
                    >
                        {title}
                    </Typography>

                    <Chip
                        label={config.label}
                        size="small"
                        sx={{
                            bgcolor: `${config.color}20`,
                            color: config.color,
                            fontWeight: 600,
                        }}
                    />
                </Stack>

                <Box>
                    <Typography
                        variant="body1"
                        fontWeight={600}
                    >
                        {primaryValue}
                    </Typography>

                    <Typography
                        variant="body2"
                        color="text.secondary"
                    >
                        {secondaryValue}
                    </Typography>
                </Box>
            </Stack>
        </Paper>
    );
};