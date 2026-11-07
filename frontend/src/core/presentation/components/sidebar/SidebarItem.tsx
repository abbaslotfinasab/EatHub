import { useState } from "react";
import { NavLink } from "react-router-dom";
import { Alert, Badge, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Tooltip, Typography } from "@mui/material";
import type { SidebarMenuItem } from "../../../domain/entities/account/SidebarMenuItem.ts";
import { useSidebar } from "../../hooks/useSidebar";

export const SidebarItem = ({ title, icon, path, badgeCount, comingSoonMessage }: SidebarMenuItem) => {
    const Icon = icon;
    const { isCollapsed } = useSidebar();
    const [noticeOpen, setNoticeOpen] = useState(false);

    const itemContent = (
        <Tooltip title={isCollapsed ? title : ""} placement="left">
            <Box sx={{
                display: "flex", alignItems: "center",
                justifyContent: isCollapsed ? "center" : "flex-start",
                gap: isCollapsed ? 0 : 2, px: isCollapsed ? 1 : 2, py: 1.5,
                mx: 1, my: 0.5, borderRadius: 3, cursor: "pointer",
                transition: "all .2s ease", bgcolor: "transparent",
                color: "rgba(255,255,255,0.8)",
                "&:hover": { bgcolor: "#254233", color: "#FFFFFF" },
            }}>
                <Badge badgeContent={badgeCount} color="error">
                    <Icon sx={{ fontSize: 24, color: "inherit" }} />
                </Badge>
                {!isCollapsed && <Typography variant="body2" sx={{
                    flex: 1, fontWeight: 500, whiteSpace: "nowrap",
                    overflow: "hidden", textOverflow: "ellipsis",
                }}>{title}</Typography>}
            </Box>
        </Tooltip>
    );

    return (
        <>
            {comingSoonMessage ? (
                <Box role="button" tabIndex={0} aria-label={title}
                    onClick={() => setNoticeOpen(true)}
                    onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            setNoticeOpen(true);
                        }
                    }}>
                    {itemContent}
                </Box>
            ) : (
                <NavLink to={path} style={{ textDecoration: "none" }}>
                    {({ isActive }) => (
                        <Box sx={{ "& > div": {
                            bgcolor: isActive ? "#1A3A28" : "transparent",
                            color: "#FFFFFF", "&:hover": { bgcolor: "#254233" },
                        } }}>
                            {itemContent}
                        </Box>
                    )}
                </NavLink>
            )}
            <Dialog open={noticeOpen} onClose={() => setNoticeOpen(false)} maxWidth="xs" fullWidth>
                <DialogTitle sx={{ fontWeight: 700 }}>{title}؛ به‌زودی در دسترس</DialogTitle>
                <DialogContent>
                    <Alert severity="info" sx={{ mt: 1, alignItems: "flex-start" }}>{comingSoonMessage}</Alert>
                </DialogContent>
                <DialogActions sx={{ px: 3, pb: 2 }}>
                    <Button onClick={() => setNoticeOpen(false)} variant="contained">متوجه شدم</Button>
                </DialogActions>
            </Dialog>
        </>
    );
};
