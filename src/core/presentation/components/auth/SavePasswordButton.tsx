// src/features/auth/presentation/components/SavePasswordButton.tsx

import Button from "@mui/material/Button";

interface Props {
    isLoading?: boolean;
}

export const SavePasswordButton = ({
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

                "&:active": {
                    transform: "scale(.98)",
                },
            }}
        >
            ذخیره رمز عبور
        </Button>
    );
};