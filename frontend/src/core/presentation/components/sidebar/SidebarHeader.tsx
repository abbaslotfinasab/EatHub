// src/core/presentation/components/sidebar/SidebarHeader.tsx

import type { MouseEvent } from "react";
import {
    Avatar,
    Box,
    IconButton,
    Tooltip,
    Typography,
} from "@mui/material";
import KeyboardArrowDownRoundedIcon from "@mui/icons-material/KeyboardArrowDownRounded";
import { useSidebar } from "../../hooks/useSidebar";

interface SidebarHeaderProps {
    restaurantName?: string;
    restaurantRole?: string;
    restaurantLogo?: string | null;
    isOpen: boolean;
    onToggle: (event: MouseEvent<HTMLElement>) => void;
}

export const SidebarHeader = ({
    restaurantName,
    restaurantLogo,
    restaurantRole,
    isOpen,
    onToggle,
}: SidebarHeaderProps) => {
    const { isCollapsed } = useSidebar();
    const name = restaurantName ?? "Business";
    const role = restaurantRole ?? "";
    const initial = name.charAt(0).toUpperCase();

    return (
        <Tooltip title={isCollapsed ? restaurantName : ""} placement="left" arrow>
            <Box
                onClick={onToggle}
                sx={{
                    px: isCollapsed ? 0 : 2,
                    py: 2,
                    cursor: "pointer",
                    userSelect: "none",
                    transition: "background-color .2s ease",
                    "&:hover": { backgroundColor: "rgba(255,255,255,0.08)" },
                }}
            >
                <Box
                    sx={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: isCollapsed ? "center" : "flex-start",
                        gap: isCollapsed ? 0 : 1.5,
                    }}
                >
                    <Avatar
                        src={restaurantLogo || undefined}
                        alt={name}
                        sx={{
                            width: 48,
                            height: 48,
                            bgcolor: "#F59E0B",
                            color: "#10281A",
                            fontWeight: 700,
                            flexShrink: 0,
                            "& .MuiAvatar-img": { objectFit: "cover" },
                        }}
                    >
                        {!restaurantLogo && initial}
                    </Avatar>

                    {!isCollapsed && (
                        <>
                            <Box sx={{ flex: 1, minWidth: 0 }}>
                                <Typography
                                    sx={{
                                        color: "#FFFFFF",
                                        fontWeight: 700,
                                        fontSize: 15,
                                        overflow: "hidden",
                                        textOverflow: "ellipsis",
                                        whiteSpace: "nowrap",
                                    }}
                                >
                                    {name}
                                </Typography>
                                <Typography sx={{ color: "rgba(255,255,255,0.65)", fontSize: 12 }}>
                                    {role}
                                </Typography>
                            </Box>
                            <IconButton
                                size="small"
                                sx={{
                                    color: "#FFFFFF",
                                    transition: "transform .25s ease",
                                    transform: isOpen ? "rotate(180deg)" : "rotate(0deg)",
                                }}
                            >
                                <KeyboardArrowDownRoundedIcon />
                            </IconButton>
                        </>
                    )}
                </Box>
            </Box>
        </Tooltip>
    );
};
