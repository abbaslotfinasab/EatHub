// src/features/auth/presentation/components/VerifyOtpButton.tsx

import Button from "@mui/material/Button";

interface Props {
    isLoading?: boolean;
}

export const VerifyOtpButton = ({
                                    isLoading = false,
                                }: Props) => {
    return (
        <Button
            fullWidth
            size="large"
            variant="contained"
            disableElevation
            loading={isLoading}
            sx={{
                height: 56,

                borderRadius: 3,

                bgcolor: "#10281A",

                fontWeight: 700,

                textTransform: "none",

                "&:hover": {
                    bgcolor: "#1A3A28",
                },
            }}
        >
            تأیید کد
        </Button>
    );
};