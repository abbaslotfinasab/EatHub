// src/core/presentation/components/sidebar/SidebarMenu.tsx

import { Fragment } from "react";

import {
        Box,
        Divider,
} from "@mui/material";

import { SidebarItem } from "./SidebarItem";
import { SidebarSection } from "./SidebarSection";

import {
        dashboardItem,
        sidebarSections,
} from "./sidebar.config";

export const SidebarMenu = () => {
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

                    {sidebarSections.map((section) => (
                        <Fragment key={section.title}>
                                <SidebarSection
                                    title={section.title}
                                />

                                {section.items.map((item) => {
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
                    ))}
            </Box>
        );
};