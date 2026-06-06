import Grid from "@mui/material/Grid";
import { Typography, Stack } from "@mui/material";

import { HealthCard } from "./HealthCard";

export const RestaurantHealth = () => {
    const items = [
        {
            title: "انبار",
            status: "success" as const,
            primaryValue: "2 کالای بحرانی",
            secondaryValue: "هیچ کالای منقضی وجود ندارد",
        },
        {
            title: "سفارشات",
            status: "warning" as const,
            primaryValue: "5 سفارش معطل",
            secondaryValue: "12 سفارش درحال آماده سازی",
        },
        {
            title: "مالی",
            status: "error" as const,
            primaryValue: "8 فاکتور پرداخت نشده",
            secondaryValue: "15,000,000 تومان بدهی",
        },
    ];

    return (
        <Stack spacing={2}>
            <Typography
                variant="h6"
                sx={{ fontWeight: 700 }}
            >
                وضعیت کلی رستوران
            </Typography>

            <Grid container spacing={3}>
                {items.map((item) => (
                    <Grid
                        key={item.title}
                        size={{
                            xs: 12,
                            md: 4,
                        }}
                    >
                        <HealthCard {...item} />
                    </Grid>
                ))}
            </Grid>
        </Stack>
    );
};