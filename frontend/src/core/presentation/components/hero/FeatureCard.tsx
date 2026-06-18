// src/features/landing/components/FeaturesSection/FeatureCard.tsx

import {
    Box,
    Paper,
    Typography,
} from "@mui/material";

interface Props {
    title: string;

    description: string;

    icon: React.ReactNode;
}

export const FeatureCard = ({
                                title,
                                description,
                                icon,
                            }: Props) => {
    return (
        <Paper
            elevation={0}
            sx={{
                p: 4,

                borderRadius: 6,

                border: "1px solid #F1F5F9",

                height: "100%",

                transition: ".25s",

                "&:hover": {
                    transform: "translateY(-4px)",

                    boxShadow:
                        "0 25px 50px rgba(15,23,42,.08)",
                },
            }}
        >
            <Box
                sx={{
                    width: 56,
                    height: 56,

                    borderRadius: 4,

                    bgcolor: "#EEF7F1",

                    color: "#10281A",

                    display: "flex",

                    alignItems: "center",

                    justifyContent: "center",

                    mb: 3,
                }}
            >
                {icon}
            </Box>

            <Typography
                sx={{
                    fontWeight: 700,

                    fontSize: 20,

                    mb: 2,
                }}
            >
                {title}
            </Typography>

            <Typography
                sx={{
                    color: "#64748B",

                    lineHeight: 2,
                }}
            >
                {description}
            </Typography>
        </Paper>
    );
};