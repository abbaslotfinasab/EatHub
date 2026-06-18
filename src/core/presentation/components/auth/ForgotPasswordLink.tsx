// src/features/auth/presentation/components/ForgotPasswordLink.tsx

import {
    Box,
    Link,
} from "@mui/material";

import { Link as RouterLink } from "react-router-dom";

export const ForgotPasswordLink = () => {
    return (
        <Box
            sx={{
                display: "flex",
                justifyContent: "flex-start",
            }}
        >
            <Link
                component={RouterLink}
                to="/forgot-password"
                underline="none"
                sx={{
                    color: "#10281A",

                    fontSize: 14,

                    fontWeight: 600,

                    transition: "color .2s ease",

                    "&:hover": {
                        color: "#1A3A28",
                    },
                }}
            >
                رمز عبور خود را فراموش کرده‌اید؟
            </Link>
        </Box>
    );
};