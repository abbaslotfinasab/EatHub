// src/core/presentation/components/navbar/logo/NavbarLogo.tsx

import { Box, Typography } from "@mui/material";
import RestaurantRoundedIcon from "@mui/icons-material/RestaurantRounded";

interface NavbarLogoProps {
    restaurantName?: string;
}

export const NavbarLogo = ({
                               restaurantName = "EatHub",
                           }: NavbarLogoProps) => {
    return (
        <Box
            sx={{
                display: "flex",
                alignItems: "center",
                gap: 1.5,
                cursor: "pointer",
                userSelect: "none",
            }}
        >
            <Box
                sx={{
                    width: 42,
                    height: 42,
                    borderRadius: 2,
                    bgcolor: "#10281A",

                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",

                    color: "#FFF",
                }}
            >
                <RestaurantRoundedIcon />
            </Box>

            <Box>
                <Typography
                    variant="subtitle1"
                    sx={{
                        fontWeight: 700,
                        lineHeight: 1.2,
                        color: "#10281A",
                    }}
                >
                    {restaurantName}
                </Typography>

                <Typography
                    variant="caption"
                    sx={{
                        color: "#6B7280",
                        display: "block",
                    }}
                >
                    Restaurant ERP
                </Typography>
            </Box>
        </Box>
    );
};