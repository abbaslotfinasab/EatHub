// src/features/auth/presentation/components/AuthCard.tsx

// src/features/auth/presentation/components/AuthCard.tsx
import type {ReactNode} from "react";

import {
    Box,
    Typography,
} from "@mui/material";

interface AuthCardProps {
    title: string;
    subtitle?: string;
    children: ReactNode;
}

export const AuthCard = ({
                             title,
                             subtitle,
                             children,
                         }: AuthCardProps) => {
    return (
        <Box
            sx={{
                width: "100%",
                maxWidth: 460,

                bgcolor: "#FFFFFF",

                border: "1px solid #E5E7EB",

                borderRadius: 6,

                p: {
                    xs: 4,
                    md: 5,
                },

                boxShadow:
                    "0 20px 50px rgba(15,23,42,.08)",
            }}
        >
            {/* Logo */}

            <Typography
                sx={{
                    textAlign: "center",

                    color: "#10281A",

                    fontSize: 28,

                    fontWeight: 800,
                }}
            >
                EatHub
            </Typography>

            {/* Title */}

            <Typography
                sx={{
                    mt: 4,

                    textAlign: "center",

                    fontSize: 30,

                    fontWeight: 700,

                    color: "#111827",
                }}
            >
                {title}
            </Typography>

            {/* Subtitle */}

            {subtitle && (
                <Typography
                    sx={{
                        mt: 1.5,

                        textAlign: "center",

                        color: "#6B7280",

                        lineHeight: 1.8,

                        fontSize: 15,
                    }}
                >
                    {subtitle}
                </Typography>
            )}

            {/* Content */}

            <Box
                sx={{
                    mt: 5,
                }}
            >
                {children}
            </Box>
        </Box>
    );
};