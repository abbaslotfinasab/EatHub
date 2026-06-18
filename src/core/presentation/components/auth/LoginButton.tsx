// src/features/auth/presentation/components/LoginButton.tsx

import Button from "@mui/material/Button";

interface Props {
    loading?: boolean;
}

export const LoginButton = ({
                                loading = false,
                            }: Props) => {
    return (
        <Button
            fullWidth
            type="submit"
            size="large"
    variant="contained"
    disableElevation
    loading={loading}
    sx={{
        mt: 1,

            height: 56,

            borderRadius: 3,

            bgcolor: "#10281A",

            fontSize: 15,
            fontWeight: 700,

            textTransform: "none",

            transition: "all .2s ease",

            "&:hover": {
            bgcolor: "#1A3A28",
        },

        "&:active": {
            transform: "scale(.98)",
        },
    }}
>
    ورود به پنل مدیریت
    </Button>
);
};