// src/features/landing/components/HeroSection/DashboardPreview.tsx

import {
    Box,
    Paper,
} from "@mui/material";

import { PreviewNavbar } from "./PreviewNavbar";
import {PreviewStats} from "./PreviewStats";
import { PreviewChart } from "./PreviewChart";
import { PreviewOrders } from "./PreviewOrders";

export const DashboardPreview = () => {
    return (
        <Paper
            elevation={0}
            sx={{
                p: {
                    xs: 2,
                    md: 4,
                },

                bgcolor: "#FFFFFF",

                borderRadius: 8,
            }}
        >
            <PreviewNavbar />

            <Box
                sx={{
                    mt: 4,
                }}
            >
                <PreviewStats />
            </Box>

            <Box
                sx={{
                    mt: 4,
                }}
            >
                <PreviewChart />
            </Box>

            <Box
                sx={{
                    mt: 4,
                }}
            >
                <PreviewOrders />
            </Box>
        </Paper>
    );
};