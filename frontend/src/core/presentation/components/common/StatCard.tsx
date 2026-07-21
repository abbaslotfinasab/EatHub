import type { ReactNode } from "react";

import {
    Box,
    Chip,
    Paper,
    Typography,
} from "@mui/material";

import TrendingUpRoundedIcon from "@mui/icons-material/TrendingUpRounded";
import TrendingDownRoundedIcon from "@mui/icons-material/TrendingDownRounded";

interface StatCardProps {
    title: string;

    value: string | number;

    subtitle?: string;

    icon?: ReactNode;

    color?: string;

    growth?: number;

    variant?: "paper" | "glass";
}

export const StatCard = ({
    title,
    value,
    subtitle,
    icon,
    color = "#2563EB",
    growth,
    variant = "paper",
}: StatCardProps) => {

    const isGlass = variant === "glass";

    const isPositive = (growth ?? 0) >= 0;

    if (isGlass) {
        return (
            <Box
                sx={{
                    minWidth: 150,

                    p: 2,

                    borderRadius: 1,

                    bgcolor: "rgba(255,255,255,.10)",

                    border: "1px solid rgba(255,255,255,.12)",

                    backdropFilter: "blur(18px)",

                    transition: ".25s",

                    display: "flex",

                    flexDirection: "column",

                    gap: 1.5,

                    "&:hover": {
                        transform: "translateY(-2px)",
                        bgcolor: "rgba(255,255,255,.15)",
                    },
                }}
            >
                <Box
                    sx={{
                        width: 38,
                        height: 38,

                        borderRadius: 2,

                        bgcolor: "rgba(255,255,255,.12)",

                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",

                        "& svg": {
                            fontSize: 20,
                            color: "#fff",
                        },
                    }}
                >
                    {icon}
                </Box>

                <Typography
                    sx={{
                        fontSize: 24,
                        fontWeight: 700,
                        color: "#fff",
                        lineHeight: 1.2,
                        wordBreak: "break-word",
                    }}
                >
                    {value}
                </Typography>

                <Typography
                    sx={{
                        fontSize: 13,
                        fontWeight: 600,
                        color: "rgba(255,255,255,.85)",
                    }}
                >
                    {title}
                </Typography>

                {subtitle && (
                    <Typography
                        sx={{
                            fontSize: 11,
                            color: "rgba(255,255,255,.65)",
                        }}
                    >
                        {subtitle}
                    </Typography>
                )}
            </Box>
        );
    }

    return (
        <Paper
            elevation={0}
            sx={{
                position: "relative",

                p: 2.5,

                height: "100%",

                borderRadius: 1,

                border: "1px solid",

                borderColor: "divider",

                overflow: "hidden",

                transition: ".25s",

                "&:hover": {
                    transform: "translateY(-3px)",

                    boxShadow: "0 12px 30px rgba(15,23,42,.06)",

                    borderColor: `${color}40`,
                },
            }}
        >
            <Box
                sx={{
                    position: "absolute",

                    top: 0,
                    left: 0,

                    width: 4,
                    height: "100%",

                    bgcolor: color,
                }}
            />

            <Box
                sx={{
                    display: "flex",

                    justifyContent: "space-between",

                    alignItems: "flex-start",

                    gap: 2,
                }}
            >
                <Box
                    sx={{
                        flex: 1,
                        minWidth: 0,
                    }}
                >
                    <Typography
                        noWrap
                        sx={{
                            fontSize: 13,
                            fontWeight: 600,
                            color: "text.secondary",
                        }}
                    >
                        {title}
                    </Typography>

                    <Typography
                        sx={{
                            mt: 1,

                            fontSize: {
                                xs: 16,
                                md: 20,
                            },

                            fontWeight: 600,

                            lineHeight: 1.2,

                            letterSpacing: "-.02em",

                        }}
                    >
                        {value}
                    </Typography>

                    {subtitle && (
                        <Typography
                            noWrap
                            sx={{
                                mt: .5,

                                fontSize: 12,

                                color: "text.secondary",
                            }}
                        >
                            {subtitle}
                        </Typography>
                    )}
                </Box>

                {icon && (
                    <Box
                        sx={{
                            width: 48,
                            height: 48,

                            flexShrink: 0,

                            borderRadius: 2.5,

                            bgcolor: `${color}12`,

                            color,

                            display: "flex",

                            alignItems: "center",

                            justifyContent: "center",

                            "& svg": {
                                fontSize: 24,
                            },
                        }}
                    >
                        {icon}
                    </Box>
                )}
            </Box>

            {growth !== undefined && (
                <Box sx={{ mt: 2 }}>
                    <Chip
                        size="small"
                        variant="outlined"
                        icon={
                            isPositive
                                ? <TrendingUpRoundedIcon/>
                                : <TrendingDownRoundedIcon/>
                        }
                        label={`${Math.abs(growth)}%`}
                        color={
                            isPositive
                                ? "success"
                                : "error"
                        }
                    />
                </Box>
            )}
        </Paper>
    );
};