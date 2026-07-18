// presentation/components/order/OrderHeader.tsx

import {
    ReceiptText,
    Save,
} from "lucide-react";

import {
    Box,
    Stack,
    Typography,
} from "@mui/material";

import { LoadingButton } from "@mui/lab";

import { useOrderForm } from "../../forms/order/useOrderForm";

interface OrderHeaderProps {
    mode: "create" | "edit";
    onCancel?: () => void;
}

export const OrderHeader = ({
    mode,
}: OrderHeaderProps) => {

    const {
        formState: {
            isSubmitting,
        },
    } = useOrderForm();

    return (

        <Box
            sx={{
                bgcolor: "#10281A",
                px: 3,
                py: 2.5,
                borderRadius: "20px 20px 0 0",
                borderBottom: "1px solid",
                borderColor: "divider",
            }}
        >

            <Stack
                sx={{
                    flexDirection: "row",
                    justifyContent: "space-between",
                    alignItems: "center",
                }}
            >

                {/* Left */}

                <Stack
                    sx={{
                        flexDirection: "row",
                        gap: 1,
                        alignItems: "center",
                    }}
                >

                    <ReceiptText
                        size={20}
                        color="rgba(255,255,255,.85)"
                    />

                    <Typography
                        sx={{
                            typography: "h6",
                            fontWeight: 600,
                            color: "white",
                        }}
                    >
                        {mode === "create"
                            ? "ثبت سفارش جدید"
                            : "ویرایش سفارش"}
                    </Typography>

                </Stack>

                {/* Right */}

                <Stack
                    sx={{
                        flexDirection: "row",
                        gap: 1.5,
                    }}
                >



                    <LoadingButton
                        loading={isSubmitting}
                        type="submit"
                        variant="contained"
                        endIcon={
                            <Save size={16} />
                        }
                        sx={{
                            bgcolor: "white",
                            color: "#10281A",

                            px: 2,
                            py: 1,

                            borderRadius: 2,

                            fontWeight: 700,

                            boxShadow: "none",

                            "& .MuiButton-endIcon": {
                                ml: 0,
                                mr: 1,
                            },

                            "&:hover": {
                                bgcolor: "grey.100",
                                boxShadow: "none",
                            },
                        }}
                    >
                        {mode === "create"
                            ? "ثبت سفارش"
                            : "ذخیره تغییرات"}
                    </LoadingButton>

                </Stack>

            </Stack>

        </Box>

    );

};