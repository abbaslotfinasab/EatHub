// src/core/presentation/components/sidebar/SidebarItem.tsx

import {NavLink} from "react-router-dom";
import {useSidebar} from "../../hooks/useSidebar";

import {
    Badge,
    Box, Tooltip,
    Typography,
} from "@mui/material";
import type {SidebarMenuItem} from "../../../domain/entities/account/SidebarMenuItem.ts";


export const SidebarItem = ({
                                title,
                                icon,
                                path,
                                badgeCount,
                            }: SidebarMenuItem) => {

    const Icon = icon;

    const {isCollapsed} = useSidebar();


    return (
        <NavLink
            to={path}
            style={{
                textDecoration: "none",
            }}
        >
            {({isActive}) => (

                <Tooltip
                    title={isCollapsed ? title : ""}
                    placement="left">


                    <Box
                        sx={{
                            display: "flex",
                            alignItems: "center",

                            justifyContent: isCollapsed
                                ? "center"
                                : "flex-start",

                            gap: isCollapsed
                                ? 0
                                : 2,

                            px: isCollapsed ? 1 : 2,
                            py: 1.5,

                            mx: 1,
                            my: 0.5,

                            borderRadius: 3,

                            cursor: "pointer",

                            transition: "all .2s ease",

                            bgcolor: isActive
                                ? "#1A3A28"
                                : "transparent",

                            color: isActive
                                ? "#FFFFFF"
                                : "rgba(255,255,255,0.8)",

                            "&:hover": {
                                bgcolor: isActive
                                    ? "#254233"
                                    : "#254233",
                                color: isActive
                                    ? "#FFFFFF"
                                    : "#FFFFFF",
                            },
                        }}
                    >
                        <Badge
                            badgeContent={badgeCount}
                            color="error"
                        >
                            <Icon
                                sx={{
                                    fontSize: 24,
                                    color: "inherit",
                                }}
                            /> </Badge>

                        {!isCollapsed && (
                            <Typography
                                variant="body2"
                                sx={{
                                    flex: 1,
                                    fontWeight: isActive
                                        ? 600
                                        : 500,

                                    whiteSpace: "nowrap",
                                    overflow: "hidden",
                                    textOverflow: "ellipsis",
                                }}
                            >
                                {title}
                            </Typography>
                        )}
                    </Box>
                </Tooltip>

            )}
        </NavLink>
    );
};