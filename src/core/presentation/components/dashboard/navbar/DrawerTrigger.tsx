import { IconButton, Tooltip } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import useMediaQuery from "@mui/material/useMediaQuery";

import MenuRoundedIcon from "@mui/icons-material/MenuRounded";

import { useSidebar } from "../../../hooks/useSidebar.ts";

export const DrawerTrigger = () => {
    const theme = useTheme();

    const isMobile = useMediaQuery(
        theme.breakpoints.down("md")
    );

    const {
        toggleCollapse,
        toggleMobile,
    } = useSidebar();

    const handleClick = () => {
        if (isMobile) {
            toggleMobile();
            return;
        }

        toggleCollapse();
    };

    return (
        <Tooltip title="منو">
            <IconButton
                onClick={handleClick}
                sx={{
                    color: "#374151",

                    "&:hover": {
                        backgroundColor: "#F3F4F6",
                    },
                }}
            >
                <MenuRoundedIcon />
            </IconButton>
        </Tooltip>
    );
};