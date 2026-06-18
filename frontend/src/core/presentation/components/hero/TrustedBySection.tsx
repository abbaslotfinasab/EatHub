// src/features/landing/components/TrustedBySection/TrustedBySection.tsx

import {
    Box,
    Container,
    Typography,
} from "@mui/material";

const brands = [
    "پیتزا هاب",
    "برگر هاب",
    "کافه هاب",
    "فودلند",
    "کافی سنتر",
    "رستوران مرکزی",
];

export const TrustedBySection = () => {
    return (
        <Container
            maxWidth="lg"
            sx={{
                py: 10,
            }}
        >
            {/* Title */}

            <Typography
                align="center"
                sx={{
                    color: "#64748B",

                    fontWeight: 600,

                    mb: 6,
                }}
            >
                بیش از ۵۰ رستوران و کافه در حال رشد با EatHub
            </Typography>

            {/* Logos */}

            <Box
                sx={{
                    display: "flex",

                    flexWrap: "wrap",

                    justifyContent: "center",

                    gap: 5,
                }}
            >
                {brands.map((brand) => (
                    <Typography
                        key={brand}
                        sx={{
                            fontSize: {
                                xs: 20,
                                md: 28,
                            },

                            fontWeight: 800,

                            color: "#CBD5E1",

                            transition: ".2s",

                            "&:hover": {
                                color: "#10281A",
                            },
                        }}
                    >
                        {brand}
                    </Typography>
                ))}
            </Box>
        </Container>
    );
};