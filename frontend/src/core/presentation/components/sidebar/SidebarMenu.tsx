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

export const SidebarMenu = () => {
        const permissions = useAuthStore((state) => state.me?.active_business?.permissions ?? []);
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
