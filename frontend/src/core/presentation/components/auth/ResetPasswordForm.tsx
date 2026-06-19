// src/features/auth/presentation/components/ResetPasswordForm.tsx

import { Box } from "@mui/material";

import { SavePasswordButton } from "./SavePasswordButton";
import { LoginLink } from "./LoginLink";

export const ResetPasswordForm = () => {
    return (
        <Box
            component="form"
            sx={{
                display: "flex",
                flexDirection: "column",
                gap: 3,
            }}
        >
            {/*<PasswordField />*/}

            {/*<ConfirmPasswordField />*/}

            <SavePasswordButton />

            <LoginLink />
        </Box>
    );
};