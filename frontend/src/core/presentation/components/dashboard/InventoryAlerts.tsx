import {
    Card,
    CardContent,
    Stack,
    Typography,
} from "@mui/material";

import ReportProblemIcon from "@mui/icons-material/ReportProblem";

import { InventoryAlertItem }
    from "./InventoryAlertItem";

export const InventoryAlerts = () => {
    const alerts = [
        {
            id: "1",
            ingredientName: "پنیر پیتزا",
            currentStock: 2,
            minimumStock: 10,
            unit: "کیلو",
            severity: "critical",
        },

        {
            id: "2",
            ingredientName: "قارچ",
            currentStock: 5,
            minimumStock: 8,
            unit: "کیلو",
            severity: "warning",
        },

        {
            id: "3",
            ingredientName: "روغن",
            currentStock: 10,
            minimumStock: 12,
            unit: "لیتر",
            severity: "low",
        },
    ];

    return (
        <Card
            elevation={0}
            sx={{
                borderRadius: 4,
                border: "1px solid",
                borderColor: "divider",
                height: "100%",
            }}
        >
            <CardContent>
                <Stack spacing={2}>
                    <Stack
                        direction="row"
                        spacing={1}
                        alignItems="center"
                    >
                        <ReportProblemIcon
                            color="warning"
                        />

                        <Typography
                            variant="h6"
                            fontWeight={700}
                        >
                            هشدارهای انبار
                        </Typography>
                    </Stack>

                    {alerts.map((alert) => (
                        <InventoryAlertItem
                            key={alert.id}
                            {...alert}
                        />
                    ))}
                </Stack>
            </CardContent>
        </Card>
    );
};