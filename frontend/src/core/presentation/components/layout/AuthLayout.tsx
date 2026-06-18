// src/features/auth/presentation/components/AuthLayout.tsx

// src/features/auth/presentation/components/AuthLayout.tsx
import type {ReactNode} from "react";

import {
    Box,
    Container,
} from "@mui/material";

import { AuthHero } from "../auth/AuthHero";

interface Props {
    children: ReactNode;
}

export const AuthLayout = ({
                               children,
                           }: Props) => {
    return (
        <Box
            sx={{
                minHeight: "100vh",
                bgcolor: "#F8FAFC",
                display: "flex",
                alignItems: "center",
            }}
        >
            <Container maxWidth="xl">
                <Box
                    sx={{
                        display: "grid",

                        gridTemplateColumns: {
                            xs: "1fr",
                            md: "1.1fr 1fr",
                        },

                        gap: 6,

                        alignItems: "center",
                    }}
                >
                    {/* Hero */}

                    <Box
                        sx={{
                            display: {
                                xs: "none",
                                md: "block",
                            },
                        }}
                    >
                        <AuthHero />
                    </Box>

                    {/* Form */}

                    <Box
                        sx={{
                            display: "flex",
                            justifyContent: "center",
                        }}
                    >
                        {children}
                    </Box>
                </Box>
            </Container>
        </Box>
    );
};