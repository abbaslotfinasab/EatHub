// src/features/business/presentation/components/BusinessCard.tsx

import { Box, Paper, Typography } from "@mui/material";
import type { ReactNode } from "react";

interface Props {
    children: ReactNode;
}

export const BusinessCard = ({
    children,
}: Props) => {
    return (
        <Box
            sx={{
                width: "100%",
                maxWidth: 720,
                mx: "auto",
            }}
        >
            {/* Header */}
            <Box
                sx={{
                    textAlign: "center",
                    mb: 5,
                }}
            >
                <Typography
                    variant="h4"
                    fontWeight={800}
                    gutterBottom
                >
                    ایجاد کسب‌وکار جدید
                </Typography>

                <Typography
                    color="text.secondary"
                    sx={{
                        maxWidth: 500,
                        mx: "auto",
                        lineHeight: 1.8,
                    }}
                >
                    تنها چند اطلاعات اولیه لازم است تا
                    فضای کاری شما آماده شود.
                </Typography>
            </Box>

            {/* Card */}
            <Paper
                elevation={0}
                sx={{
                    p: {
                        xs: 3,
                        md: 5,
                    },

                    borderRadius: 6,

                    border: "1px solid",
                    borderColor: "divider",

                    bgcolor: "background.paper",

                    boxShadow:
                        "0px 20px 60px rgba(0,0,0,.06)",
                }}
            >
                {children}
            </Paper>

            {/* Footer */}
            <Typography
                variant="body2"
                color="text.secondary"
                textAlign="center"
                sx={{
                    mt: 3,
                }}
            >
                بعداً می‌توانید تمام این اطلاعات را
                از بخش تنظیمات تغییر دهید.
            </Typography>
        </Box>
    );
};