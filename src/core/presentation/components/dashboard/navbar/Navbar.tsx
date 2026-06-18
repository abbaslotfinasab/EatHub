// src/core/presentation/components/navbar/Navbar.tsx

import {
    AppBar,
    Toolbar,
    Box,
} from "@mui/material";

import { DrawerTrigger } from "./DrawerTrigger.tsx";
import { NavbarLogo } from "./NavbarLogo.tsx";
import { NavbarSearch } from "./NavbarSearch.tsx";
import { NotificationButton } from "./NotificationButton.tsx";
import { UserMenu } from "./UserMenu.tsx";

import { useSidebar } from "../../../hooks/useSidebar.ts";

import {
    NAVBAR_HEIGHT,
    SIDEBAR_WIDTH,
    SIDEBAR_COLLAPSED_WIDTH,
} from "../../../../../config/constants.ts";

export const Navbar = () => {
    const { isCollapsed } = useSidebar();

    const sidebarWidth = isCollapsed
        ? SIDEBAR_COLLAPSED_WIDTH
        : SIDEBAR_WIDTH;

    return (
        <AppBar
            position="fixed"
            elevation={0}
            sx={{
                width: {
                    xs: "100%",
                    md: `calc(100% - ${sidebarWidth}px)`,
                },

                right: {
                    xs: 0,
                    md: `${sidebarWidth}px`,
                },

                height: `${NAVBAR_HEIGHT}px`,

                bgcolor: "#FFFFFF",

                color: "#111827",

                borderBottom: "1px solid #E5E7EB",

                transition:
                    "width 0.3s ease, right 0.3s ease",

                zIndex: 1100,
            }}
        >
            <Toolbar
                sx={{
                    minHeight: `${NAVBAR_HEIGHT}px !important`,

                    px: {
                        xs: 2,
                        md: 3,
                    },

                    gap: 2,
                }}
            >
                {/* Collapse Sidebar */}

                <DrawerTrigger />

                {/* Logo */}

                <NavbarLogo />

                {/* Search */}

                <NavbarSearch />

                {/* Spacer */}

                <Box
                    sx={{
                        flexGrow: 1,
                    }}
                />

                {/* Notifications */}

                <NotificationButton />

                {/* User */}

                <UserMenu />
            </Toolbar>
        </AppBar>
    );
};