// src/features/landing/pages/HomePage.tsx

import { Box } from "@mui/material";
import {HeroSection} from "../components/hero/HeroSection.tsx";
import {Navbar} from "../components/navbar/Navbar.tsx";
import {TrustedBySection} from "../components/hero/TrustedBySection.tsx";
import {FeaturesSection} from "../components/hero/FeaturesSection.tsx";
import {ModulesSection} from "../components/hero/ModulesSection.tsx";


export const HomePage = () => {
    return (
        <Box
            sx={{
                minHeight: "100vh",

                bgcolor: "#FFFFFF",

                overflowX: "hidden",
            }}
        >

            <Navbar />

            {/* Hero */}

            <HeroSection />

            {/* TrustedBySection */}
            <TrustedBySection />


            {/* FeaturesSection */}
            <FeaturesSection />
            {/* DashboardSection */}

            {/* ModulesSection */}
            <ModulesSection/>

            {/* TestimonialsSection */}

            {/* PricingSection */}

            {/* FAQSection */}

            {/* CTASection */}

            {/* Footer */}
        </Box>
    );
};