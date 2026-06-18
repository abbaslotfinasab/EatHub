// src/core/presentation/components/sidebar/SidebarFooter.tsx

import {
    Box,
    Divider,
    List,
    ListItemButton,
    ListItemIcon,
    ListItemText,
} from "@mui/material";

import SettingsRoundedIcon from "@mui/icons-material/SettingsRounded";
import PaletteRoundedIcon from "@mui/icons-material/PaletteRounded";
import HelpOutlineRoundedIcon from "@mui/icons-material/HelpOutlineRounded";
import LogoutRoundedIcon from "@mui/icons-material/LogoutRounded";

import { useNavigate } from "react-router-dom";

export const SidebarFooter = () => {
    const navigate = useNavigate();

    const handleLogout = () => {
        // logout usecase
        // clear token
        // redirect login

        navigate("/login");
    };

    return (
        <Box>
            <Divider />

            <List disablePadding>
                <ListItemButton
                    onClick={() =>
                        navigate("/settings")
                    }
                >
                    <ListItemIcon>
                        <SettingsRoundedIcon />
                    </ListItemIcon>

                    <ListItemText
                        primary="تنظیمات"
                    />
                </ListItemButton>

                <ListItemButton>
                    <ListItemIcon>
                        <PaletteRoundedIcon />
                    </ListItemIcon>

                    <ListItemText
                        primary="ظاهر"
                    />
                </ListItemButton>

                <ListItemButton>
                    <ListItemIcon>
                        <HelpOutlineRoundedIcon />
                    </ListItemIcon>

                    <ListItemText
                        primary="راهنما"
                    />
                </ListItemButton>

                <Divider />

                <ListItemButton
                    onClick={handleLogout}
                    sx={{
                        color: "error.main",

                        "& .MuiListItemIcon-root": {
                            color: "error.main",
                        },
                    }}
                >
                    <ListItemIcon>
                        <LogoutRoundedIcon />
                    </ListItemIcon>

                    <ListItemText
                        primary="خروج از حساب"
                    />
                </ListItemButton>
            </List>
        </Box>
    );
};