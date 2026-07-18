import ShoppingCartOutlinedIcon from "@mui/icons-material/ShoppingCartOutlined";

import {
    Paper,
    Stack,
    Typography,
} from "@mui/material";

export const EmptySelectedItems = () => {
    return (
        <Paper
            variant="outlined"
            sx={{
                p: 5,
                borderRadius: 3,
                borderStyle: "dashed",
            }}
        >
            <Stack
                sx={{
                    alignItems: "center",
                    textAlign: "center",
                    gap: 2,
                }}
            >
                <ShoppingCartOutlinedIcon
                    sx={{
                        fontSize: 72,
                        color: "text.disabled",
                    }}
                />

                <Typography
                    variant="h6"
                    sx={{
                        fontWeight: 700,
                    }}
                >
                    هنوز آیتمی انتخاب نشده است
                </Typography>

                <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{
                        maxWidth: 360,
                        lineHeight: 1.8,
                    }}
                >
                    از لیست منو، غذا یا نوشیدنی موردنظر را انتخاب کنید تا
                    سفارش شما تشکیل شود.
                </Typography>
            </Stack>
        </Paper>
    );
};