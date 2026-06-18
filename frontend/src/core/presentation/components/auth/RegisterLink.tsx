// src/features/auth/presentation/components/RegisterLink.tsx

import {
    Box,
    Link,
    Typography,
} from "@mui/material";

import { Link as RouterLink } from "react-router-dom";

export const RegisterLink = () => {
    return (
        <Box
            sx={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                gap: 1,
                mt: 1,
            }}
        >
            <Typography
                variant="body2"
                sx={{
                    color: "#6B7280",
                }}
            >
                حساب کاربری ندارید؟
            </Typography>

            <Link
                component={RouterLink}
                to="/register"
                underline="none"
                sx={{
                    color: "#10281A",
                    fontWeight: 700,

                    transition: "all .2s ease",

                    "&:hover": {
                        color: "#1A3A28",
                    },
                }}
            >
                ثبت‌نام
            </Link>
        </Box>
    );
};