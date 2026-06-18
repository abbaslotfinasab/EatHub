// src/features/landing/components/HeroSection/DashboardPreview/PreviewNavbar.tsx

import {
    Avatar,
    Box,
    Typography,
} from "@mui/material";

import NotificationsNoneRoundedIcon
    from "@mui/icons-material/NotificationsNoneRounded";

export const PreviewNavbar = () => {
    return (
        <Box
            sx={{
                display: "flex",
                alignItems: "center",

                justifyContent: "space-between",

                pb: 3,

                borderBottom:
                    "1px solid #F1F5F9",
            }}
        >
            {/* Left */}

            <Box>
                <Typography
                    sx={{
                        fontWeight: 700,

                        fontSize: {
                            xs: 18,
                            md: 24,
                        },

                        color: "#0F172A",
                    }}
                >
                    داشبورد
                </Typography>

                <Typography
                    sx={{
                        mt: .5,

                        color: "#64748B",

                        fontSize: 14,
                    }}
                >
                    امروز، ۲۴ مرداد
                </Typography>
            </Box>

            {/* Right */}

            <Box
                sx={{
                    display: "flex",

                    alignItems: "center",

                    gap: 2,
                }}
            >
                <Box
                    sx={{
                        width: 40,
                        height: 40,

                        borderRadius: 3,

                        display: "flex",

                        alignItems: "center",

                        justifyContent: "center",

                        bgcolor: "#F8FAFC",

                        color: "#475569",
                    }}
                >
                    <NotificationsNoneRoundedIcon />
                </Box>

                <Box
                    sx={{
                        display: "flex",

                        alignItems: "center",

                        gap: 1.5,
                    }}
                >
                    <Avatar
                        sx={{
                            width: 40,
                            height: 40,

                            bgcolor: "#10281A",

                            fontWeight: 700,
                        }}
                    >
                        ع
                    </Avatar>

                    <Box>
                        <Typography
                            sx={{
                                fontWeight: 600,

                                fontSize: 14,

                                color: "#0F172A",
                            }}
                        >
                            عباس
                        </Typography>

                        <Typography
                            sx={{
                                color: "#64748B",

                                fontSize: 12,
                            }}
                        >
                            مدیر
                        </Typography>
                    </Box>
                </Box>
            </Box>
        </Box>
    );
};