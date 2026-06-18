// src/core/presentation/components/sidebar/SidebarSection.tsx

import { Typography } from "@mui/material";

interface SidebarSectionProps {
    title: string;
}

export const SidebarSection = ({
                                   title,
                               }: SidebarSectionProps) => {
    return (
        <Typography
            sx={{
                px: 3,
                py: 1.5,

                color:
                    "rgba(255,255,255,0.45)",

                fontSize: 11,

                fontWeight: 700,

                letterSpacing: ".08em",

                textTransform: "uppercase",
            }}
        >
            {title}
        </Typography>
    );
};