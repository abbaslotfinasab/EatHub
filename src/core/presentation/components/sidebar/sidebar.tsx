// src/core/presentation/components/sidebar/Sidebar.tsx

import { useTheme } from "@mui/material/styles";
import useMediaQuery from "@mui/material/useMediaQuery";

import { DesktopSidebar } from "./DesktopSidebar";
import { MobileSidebar } from "./MobileSidebar";

export const Sidebar = () => {
    const theme = useTheme();

    const isMobile = useMediaQuery(
        theme.breakpoints.down("md")
    );

    if (isMobile) {
        return <MobileSidebar />;
    }

    return <DesktopSidebar />;
};