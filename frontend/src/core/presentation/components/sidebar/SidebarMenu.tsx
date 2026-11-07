// src/core/presentation/components/sidebar/SidebarMenu.tsx

import { Fragment } from "react";

import {
        Box,
        Divider,
} from "@mui/material";

import { SidebarItem } from "./SidebarItem";
import { SidebarSection } from "./SidebarSection";
import { useAuthStore } from "../../store/auth.store";

import {
        dashboardItem,
        sidebarSections,
} from "./sidebar.config";

// Keep the fallback reference stable. Returning [] from a Zustand selector
// creates a new snapshot on every read when the user has no active business,
// which can trigger an infinite React render loop on routes such as /business.
const EMPTY_PERMISSIONS: string[] = [];

export const SidebarMenu = () => {
        const storedPermissions = useAuthStore(
            (state) => state.me?.active_business?.permissions,
        );
        const permissions = storedPermissions ?? EMPTY_PERMISSIONS;
        const DashboardIcon = dashboardItem.icon;

        return (
            <Box sx={{ py: 1 }}>
                    {/* Dashboard */}

                    <SidebarItem
                        title={dashboardItem.title}
                        path={dashboardItem.path}
                        icon={DashboardIcon}
                    />

                    <Divider
                        sx={{
                                my: 1.5,
                                borderColor: "rgba(255,255,255,0.08)",
                        }}
                    />

                    {/* Sections */}

                    {sidebarSections.map((section) => {
                        const visibleItems = section.items.filter(
                            (item) => !item.requiredPermission || permissions.includes(item.requiredPermission),
                        );
                        if (visibleItems.length === 0) return null;

                        return (
                        <Fragment key={section.title}>
                                <SidebarSection
                                    title={section.title}
                                />

                                {visibleItems.map((item) => {
                                        const Icon = item.icon;

                                        return (
                                            <SidebarItem
                                                key={item.path}
                                                title={item.title}
                                                path={item.path}
                                                icon={Icon}
                                                comingSoonMessage={item.comingSoonMessage}
                                            />
                                        );
                                })}

                                <Divider
                                    sx={{
                                            my: 1.5,
                                            borderColor:
                                                "rgba(255,255,255,0.08)",
                                    }}
                                />
                        </Fragment>
                        );
                    })}
            </Box>
        );
};
