import {useState} from "react";
import {useNavigate} from "react-router-dom";
import {
    Avatar, Box, Divider, Menu, MenuItem, Stack, Typography,
} from "@mui/material";
import PersonOutlineRoundedIcon from "@mui/icons-material/PersonOutlineRounded";
import SettingsRoundedIcon from "@mui/icons-material/SettingsRounded";
import LogoutRoundedIcon from "@mui/icons-material/LogoutRounded";
import KeyboardArrowDownRoundedIcon from "@mui/icons-material/KeyboardArrowDownRounded";
import {useAuthStore} from "../../../store/auth.store.ts";
import {useLogout} from "../../../hooks/useLogout.ts";

export const UserMenu = () => {
    const me = useAuthStore((state) => state.me);
    const logout = useLogout();
    const navigate = useNavigate();
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const initials = me?.name?.trim()?.charAt(0)?.toUpperCase() || "U";

    const handleClose = () => setAnchorEl(null);

    return (
        <>
            <Box
                onClick={(event) => setAnchorEl(event.currentTarget)}
                sx={{
                    display: "flex", alignItems: "center", gap: 1,
                    px: 1.5, py: 0.75, borderRadius: 2, cursor: "pointer",
                    "&:hover": {backgroundColor: "#F3F4F6"},
                }}
            >
                <Avatar src={me?.avatar ?? undefined} sx={{width: 40, height: 40, bgcolor: "#10281A", fontWeight: 700}}>
                    {initials}
                </Avatar>
                <Box sx={{display: {xs: "none", md: "block"}}}>
                    <Typography variant="body2" sx={{fontWeight: 600, lineHeight: 1.2}}>
                        {me?.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                        {me?.email}
                    </Typography>
                </Box>
                <KeyboardArrowDownRoundedIcon sx={{color: "#6B7280"}}/>
            </Box>

            <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleClose}
                anchorOrigin={{vertical: "bottom", horizontal: "right"}}
                transformOrigin={{vertical: "top", horizontal: "right"}}
                slotProps={{paper: {sx: {minWidth: 260, borderRadius: 3, mt: 1}}}}
            >
                <Box sx={{px: 2, py: 1.5}}>
                    <Stack direction="row" alignItems="center" gap={1.5}>
                        <Avatar src={me?.avatar ?? undefined} sx={{bgcolor: "#10281A"}}>
                            {initials}
                        </Avatar>
                        <Box>
                            <Typography sx={{fontWeight: 600}}>{me?.name}</Typography>
                            <Typography variant="caption" color="text.secondary">{me?.email}</Typography>
                        </Box>
                    </Stack>
                </Box>
                <Divider/>
                <MenuItem onClick={() => {handleClose(); navigate("/profile");}}>
                    <PersonOutlineRoundedIcon sx={{mr: 1, fontSize: 20}}/>
                    پروفایل
                </MenuItem>
                <MenuItem onClick={() => {handleClose(); navigate("/settings/inventory");}}>
                    <SettingsRoundedIcon sx={{mr: 1, fontSize: 20}}/>
                    تنظیمات
                </MenuItem>
                <Divider/>
                <MenuItem onClick={() => {handleClose(); logout();}} sx={{color: "error.main"}}>
                    <LogoutRoundedIcon sx={{mr: 1, fontSize: 20}}/>
                    خروج از حساب
                </MenuItem>
            </Menu>
        </>
    );
};
