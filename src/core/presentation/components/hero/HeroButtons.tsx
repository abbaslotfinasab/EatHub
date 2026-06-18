// src/features/landing/components/HeroSection/HeroButtons.tsx

import {
    Box,
    Button,
} from "@mui/material";

import ArrowOutwardRoundedIcon
    from "@mui/icons-material/ArrowOutwardRounded";

import PlayArrowRoundedIcon
    from "@mui/icons-material/PlayArrowRounded";

export const HeroButtons = () => {
    return (
        <Box
            sx={{
                display: "flex",

                justifyContent: "center",

                flexDirection: {
                    xs: "column",
                    sm: "row",
                },

                gap: 2,
            }}
        >
            {/* Primary CTA */}

            <Button
                variant="contained"
                size="large"
                endIcon={<ArrowOutwardRoundedIcon />}
                sx={{
                    height: 56,

                    px: 4,

                    borderRadius: 100,

                    bgcolor: "#10281A",

                    fontWeight: 700,

                    textTransform: "none",

                    boxShadow: "none",

                    "&:hover": {
                        bgcolor: "#1A3A28",

                        boxShadow: "none",
                    },
                }}
            >
                شروع رایگان
            </Button>

            {/* Secondary CTA */}

            <Button
                variant="outlined"
                size="large"
                startIcon={<PlayArrowRoundedIcon />}
                sx={{
                    height: 56,

                    px: 4,

                    borderRadius: 100,

                    textTransform: "none",

                    fontWeight: 700,

                    borderColor: "#E5E7EB",

                    color: "#111827",

                    "&:hover": {
                        borderColor: "#D1D5DB",

                        bgcolor: "#F9FAFB",
                    },
                }}
            >
                مشاهده دموی محصول
            </Button>
        </Box>
    );
};