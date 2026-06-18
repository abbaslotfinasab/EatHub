// src/features/landing/components/HeroSection/HeroImage.tsx

import {
    Box,
    Paper,
} from "@mui/material";
import {DashboardPreview} from "./dashboard/DashboardPreview.tsx";



export const HeroImage = () => {
    return (
        <Box
            sx={{
                position: "relative",

                maxWidth: 1200,

                mx: "auto",
            }}
        >
            {/* Glow */}

            <Box
                sx={{
                    position: "absolute",

                    top: -80,
                    left: "50%",

                    transform:
                        "translateX(-50%)",

                    width: 500,
                    height: 500,

                    borderRadius: "50%",

                    background:
                        "radial-gradient(rgba(16,40,26,.18),transparent)",

                    filter: "blur(100px)",

                    zIndex: 0,
                }}
            />

            {/* Dashboard */}

            <Paper
                elevation={0}
                sx={{
                    position: "relative",

                    zIndex: 1,

                    overflow: "hidden",

                    borderRadius: 8,

                    border:
                        "1px solid #E5E7EB",

                    bgcolor: "#FFF",

                    boxShadow:
                        "0 40px 100px rgba(15,23,42,.12)",
                }}
            >
                <DashboardPreview />
            </Paper>
        </Box>
    );
};