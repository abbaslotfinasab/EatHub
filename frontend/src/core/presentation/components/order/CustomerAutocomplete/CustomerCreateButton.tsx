// presentation/components/order/customer/CustomerCreateButton.tsx

import AddRoundedIcon from "@mui/icons-material/AddRounded";

import {
    Box,
    ButtonBase,
    Stack,
    Typography,
} from "@mui/material";

interface CustomerCreateButtonProps {
    search: string;

    onClick: () => void;
}

export const CustomerCreateButton = ({
                                         search,
                                         onClick,
                                     }: CustomerCreateButtonProps) => {

    return (

        <ButtonBase
            onClick={onClick}
            sx={{
                width: "100%",

                justifyContent: "flex-start",

                textAlign: "right",

                borderTop: "1px solid",

                borderColor: "divider",

                px: 2,

                py: 1.5,

                transition: ".2s",

                "&:hover": {
                    bgcolor: "primary.50",
                },
            }}
        >

            <Stack
                sx={{
                    flexDirection: "row",
                    gap: 2,
                    alignItems: "center",
                }}
            >
                <Box
                    sx={{
                        width: 40,
                        height: 40,

                        borderRadius: "50%",

                        bgcolor: "primary.main",

                        color: "#fff",

                        display: "flex",

                        alignItems: "center",

                        justifyContent: "center",
                    }}
                >

                    <AddRoundedIcon/>

                </Box>

                <Stack>

                    <Typography
                        sx={{
                            fontWeight: 700,
                        }}
                    >
                        ایجاد مشتری جدید
                    </Typography>

                    {search && (

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            {search}
                        </Typography>

                    )}

                </Stack>

            </Stack>

        </ButtonBase>

    );

};