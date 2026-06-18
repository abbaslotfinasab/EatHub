// src/features/auth/presentation/components/ResendCodeButton.tsx

import {
    Box,
    Link,
    Typography,
} from "@mui/material";

export const ResendCodeButton = () => {
    return (
        <Box
            sx={{
                display: "flex",
                justifyContent: "center",
                gap: 1,
            }}
        >
            <Typography
                variant="body2"
                color="#6B7280"
            >
                کد را دریافت نکردید؟
            </Typography>

            <Link
                underline="none"
                sx={{
                    cursor: "pointer",

                    color: "#10281A",

                    fontWeight: 700,

                    "&:hover": {
                        color: "#1A3A28",
                    },
                }}
            >
                ارسال مجدد
            </Link>
        </Box>
    );
};