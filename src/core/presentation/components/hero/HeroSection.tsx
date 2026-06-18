// src/features/landing/components/HeroSection/HeroSection.tsx

import { Container } from "@mui/material";

import { HeroContent } from "./HeroContent";
import { HeroImage } from "./HeroImage";

export const HeroSection = () => {
    return (
        <Container
            maxWidth="xl"
            sx={{
                pt: {
                    xs: 12,
                    md: 18,
                },

                pb: 12,
            }}
        >
            <HeroContent />

            <HeroImage />
        </Container>
    );
};