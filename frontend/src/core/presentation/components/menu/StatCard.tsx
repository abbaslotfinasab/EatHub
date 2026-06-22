import { Box, Typography } from "@mui/material";
import type { ReactNode } from "react";

interface StatCardProps {
    title: string;
    value?: string | number;
    icon?: ReactNode;
}

export const StatCard = ({
    title,
    value,
    icon,
}: StatCardProps) => {
    return (
        <Box
            sx={{
                minWidth: 130,

                px: 2.5,
                py: 2,

                borderRadius: 4,

                background:
                    "rgba(255,255,255,.10)",

                border:
                    "1px solid rgba(255,255,255,.12)",

                backdropFilter:
                    "blur(16px)",

                transition: ".25s",

                display: "flex",
                flexDirection: "column",
                gap: 1,

                "&:hover": {
                    transform:
                        "translateY(-2px)",

                    background:
                        "rgba(255,255,255,.15)",

                    border:
                        "1px solid rgba(255,255,255,.20)",
                },
            }}
        >
            <Box
                sx={{
                    display: "flex",
                    justifyContent:
                        "space-between",
                    alignItems:
                        "center",
                }}
            >
                <Typography
                    sx={{
                        fontSize: 13,
                        color:
                            "rgba(255,255,255,.75)",
                        fontWeight: 500,
                    }}
                >
                    {title}
                </Typography>

                {icon && (
                    <Box
                        sx={{
                            width: 32,
                            height: 32,

                            borderRadius:
                                "12px",

                            display: "flex",
                            alignItems:
                                "center",
                            justifyContent:
                                "center",

                            bgcolor:
                                "rgba(255,255,255,.12)",

                            "& svg": {
                                fontSize: 18,
                                color: "#fff",
                            },
                        }}
                    >
                        {icon}
                    </Box>
                )}
            </Box>

            <Typography
                sx={{
                    fontSize: 28,
                    lineHeight: 1,

                    fontWeight: 900,

                    color: "#fff",
                }}
            >
                {value}
            </Typography>
        </Box>
    );
};