// src/features/auth/presentation/components/SendCodeButton.tsx

import Button from "@mui/material/Button";

interface Props {
    isLoading?: boolean;
}

export const SendCodeButton = ({
                                   isLoading = false,
                               }: Props) => {
    return (
        <Button
            fullWidth
            variant="contained"
            size="large"
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
            ارسال کد تأیید
        </Button>
    );
};