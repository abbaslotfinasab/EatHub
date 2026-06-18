// src/features/landing/components/HeroSection/DashboardPreview/PreviewOrders.tsx

import {
    Avatar,
    Box,
    Paper,
    Stack,
    Typography,
} from "@mui/material";

const orders = [
    {
        id: "#2415",
        name: "پیتزا پپرونی",
        price: "120,000",
        emoji: "🍕",
    },
    {
        id: "#2416",
        name: "برگر مخصوص",
        price: "180,000",
        emoji: "🍔",
    },
    {
        id: "#2417",
        name: "لاته",
        price: "95,000",
        emoji: "☕",
    },
    {
        id: "#2418",
        name: "پاستا آلفردو",
        price: "210,000",
        emoji: "🍝",
    },
];

export const PreviewOrders = () => {
    return (
        <Paper
            elevation={0}
            sx={{
                p: 4,

                borderRadius: 5,

                border: "1px solid #F1F5F9",
            }}
        >
            <Typography
                sx={{
                    mb: 4,

                    fontWeight: 700,

                    fontSize: 18,
                }}
            >
                سفارشات اخیر
            </Typography>

            <Stack spacing={3}>
                {orders.map((order) => (
                    <Box
                        key={order.id}
                        sx={{
                            display: "flex",

                            alignItems: "center",

                            justifyContent: "space-between",
                        }}
                    >
                        {/* Right */}

                        <Box
                            sx={{
                                display: "flex",

                                alignItems: "center",

                                gap: 2,
                            }}
                        >
                            <Avatar
                                sx={{
                                    bgcolor: "#F8FAFC",

                                    width: 48,

                                    height: 48,

                                    fontSize: 24,
                                }}
                            >
                                {order.emoji}
                            </Avatar>

                            <Box>
                                <Typography
                                    sx={{
                                        fontWeight: 600,
                                    }}
                                >
                                    {order.name}
                                </Typography>

                                <Typography
                                    sx={{
                                        color: "#64748B",

                                        fontSize: 13,
                                    }}
                                >
                                    {order.id}
                                </Typography>
                            </Box>
                        </Box>

                        {/* Left */}

                        <Typography
                            sx={{
                                fontWeight: 700,

                                color: "#0F172A",
                            }}
                        >
                            {order.price} تومان
                        </Typography>
                    </Box>
                ))}
            </Stack>
        </Paper>
    );
};