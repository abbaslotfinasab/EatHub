import {
    Box,
    Chip,
    Stack,
    Typography,
} from "@mui/material";

interface Props {
    ingredientName: string;
    currentStock: number;
    minimumStock: number;
    unit: string;
    severity:
        | "critical"
        | "warning"
        | "low";
}

const severityConfig = {
    critical: {
        color: "#EF4444",
        label: "بحرانی",
    },

    warning: {
        color: "#F97316",
        label: "کمبود",
    },

    low: {
        color: "#EAB308",
        label: "رو به اتمام",
    },
};

export const InventoryAlertItem = ({
                                       ingredientName,
                                       currentStock,
                                       minimumStock,
                                       unit,
                                       severity,
                                   }: Props) => {
    const config =
        severityConfig[severity];

    return (
        <Box
            sx={{
                p: 2,
                borderRadius: 3,
                border: "1px solid",
                borderColor: "divider",
            }}
        >
            <Stack
                direction="row"
                justifyContent="space-between"
                alignItems="center"
                mb={1}
            >
                <Typography
                    fontWeight={600}
                >
                    {ingredientName}
                </Typography>

                <Chip
                    label={config.label}
                    size="small"
                    sx={{
                        bgcolor:
                            `${config.color}20`,
                        color: config.color,
                        fontWeight: 600,
                    }}
                />
            </Stack>

            <Typography
                variant="body2"
                color="text.secondary"
            >
                موجودی فعلی:
                {" "}
                {currentStock}
                {" "}
                {unit}
            </Typography>

            <Typography
                variant="body2"
                color="text.secondary"
            >
                حداقل مجاز:
                {" "}
                {minimumStock}
                {" "}
                {unit}
            </Typography>
        </Box>
    );
};