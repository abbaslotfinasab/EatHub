// src/features/auth/presentation/components/ForgotPasswordForm.tsx

import { Box } from "@mui/material";

import { PhoneField } from "./PhoneField";
import { SendCodeButton } from "./SendCodeButton";
import { LoginLink } from "./LoginLink";

export const ForgotPasswordForm = () => {
    return (
        <Box
            component="form"
            sx={{
                display: "flex",
                flexDirection: "column",
                gap: 3,
            }}
        >
            <PhoneField />

            <SendCodeButton />

            <LoginLink />
        </Box>
    );
};