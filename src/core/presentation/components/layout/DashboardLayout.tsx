// DashboardLayout.tsx

import { Outlet } from "react-router-dom";

import { Box } from "@mui/material";

import { Navbar } from "../dashboard/navbar/Navbar";


import {
    SIDEBAR_WIDTH,
    SIDEBAR_COLLAPSED_WIDTH, NAVBAR_HEIGHT,
} from "../../../../config/constants";

import { useSidebar } from "../../hooks/useSidebar";
import {Sidebar} from "../sidebar/sidebar.tsx";
import { useTheme } from "@mui/material/styles";
import useMediaQuery from "@mui/material/useMediaQuery";


export const DashboardLayout = () => {
    const { isCollapsed } = useSidebar();

    const theme = useTheme();

    const isMobile = useMediaQuery(
        theme.breakpoints.down("md")
    );

    const sidebarWidth = isCollapsed
        ? SIDEBAR_COLLAPSED_WIDTH
        : SIDEBAR_WIDTH;

    return (
        <>
            <Sidebar />

            <Navbar />

            <Box
                sx={{
                    mr: isMobile
                        ? 0
                        : `${sidebarWidth}px`,

                    pt: `${NAVBAR_HEIGHT}px`,

                    minHeight: "100vh",

                    transition:
                        "margin-right .3s ease",

                    bgcolor: "#F8FAFC",
                }}
            >
                <Box sx={{ p: 3 }}>
                    <Outlet />
                </Box>
            </Box>
        </>
    );
};