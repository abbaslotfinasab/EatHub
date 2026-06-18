// src/features/auth/presentation/components/VerifyOtpForm.tsx

import { Box } from "@mui/material";

import { OtpField } from "./OtpField";
import { VerifyOtpButton } from "./VerifyOtpButton";
import { ResendCodeButton } from "./ResendCodeButton";

export const VerifyOtpForm = () => {
    return (
        <Box
            component="form"
            sx={{
                display: "flex",
                flexDirection: "column",
                gap: 4,
            }}
        >
            <OtpField />

            <VerifyOtpButton />

            <ResendCodeButton />
        </Box>
    );
};