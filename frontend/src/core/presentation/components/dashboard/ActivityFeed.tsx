import {
    Card,
    CardContent,
    Divider,
    Stack,
    Typography,
} from "@mui/material";

import HomeIcon from "@mui/icons-material/Home";

import { ActivityItem }
    from "./ActivityItem";

export const ActivityFeed = () => {
    const activities = [
        {
            id: "1",
            userName: "عباس لطفی نسب",
            action: "سفارش #1024 را ثبت کرد",
            timestamp: "2 دقیقه قبل",
            type: "order" as const,
        },

        {
            id: "2",
            userName: "محمد رضایی",
            action: "50 کیلو مرغ وارد انبار کرد",
            timestamp: "12 دقیقه قبل",
            type: "inventory" as const,
        },

        {
            id: "3",
            userName: "سارا احمدی",
            action: "فاکتور خرید #125 را ثبت کرد",
            timestamp: "18 دقیقه قبل",
            type: "accounting" as const,
        },

        {
            id: "4",
            userName: "علی کریمی",
            action: "رزرو جدید ثبت کرد",
            timestamp: "35 دقیقه قبل",
            type: "reservation" as const,
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
                <Stack spacing={3}>
                    <Stack
                        direction="row"
                        spacing={1}
                        alignItems="center"
                    >
                        <HomeIcon />

                        <Typography
                            variant="h6"
                            sx={{ fontWeight: 700 }}
                        >
                            فعالیت‌های اخیر
                        </Typography>
                    </Stack>

                    {activities.map(
                        (activity, index) => (
                            <Stack
                                key={activity.id}
                                spacing={2}
                            >
                                <ActivityItem
                                    {...activity}
                                />

                                {index !==
                                    activities.length -
                                    1 && (
                                        <Divider />
                                    )}
                            </Stack>
                        )
                    )}
                </Stack>
            </CardContent>
        </Card>
    );
};