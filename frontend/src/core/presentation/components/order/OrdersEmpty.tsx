import ReceiptLongRoundedIcon from "@mui/icons-material/ReceiptLongRounded";
import SearchOffRoundedIcon from "@mui/icons-material/SearchOffRounded";

import {
    Box,
    Button,
    Paper,
    Stack,
    Typography,
} from "@mui/material";

interface OrdersEmptyProps {
    hasFilters?: boolean;
    onResetFilters?: () => void;
}

export const OrdersEmpty = ({
                                hasFilters = false,
                                onResetFilters,
                            }: OrdersEmptyProps) => {
    return (
        <Paper
            elevation={0}
            sx={{
                py: 8,
                px: 4,
                borderRadius: 3,
                border: "1px dashed",
                borderColor: "divider",
            }}
        >
            <Stack
                sx={{
                    alignItems: "center",
                    textAlign: "center",
                    gap: 3,
                }}
            >
                <Box
                    sx={{
                        width: 72,
                        height: 72,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        borderRadius: "50%",
                        bgcolor: "action.hover",
                    }}
                >
                    {hasFilters ? (
                        <SearchOffRoundedIcon
                            sx={{
                                fontSize: 36,
                                color: "text.secondary",
                            }}
                        />
                    ) : (
                        <ReceiptLongRoundedIcon
                            sx={{
                                fontSize: 36,
                                color: "text.secondary",
                            }}
                        />
                    )}
                </Box>

                <Stack spacing={1}>
                    <Typography
                        variant="h6"
                        sx={{
                            fontWeight: 700,
                        }}
                    >
                        {hasFilters
                            ? "سفارشی پیدا نشد"
                            : "هنوز سفارشی ثبت نشده است"}
                    </Typography>

                    <Typography
                        variant="body2"
                        sx={{
                            color: "text.secondary",
                            maxWidth: 420,
                        }}
                    >
                        {hasFilters
                            ? "هیچ سفارشی با فیلترهای انتخاب‌شده مطابقت ندارد. فیلترها یا عبارت جستجو را تغییر دهید."
                            : "پس از ثبت اولین سفارش، اطلاعات آن در این بخش نمایش داده خواهد شد."}
                    </Typography>
                </Stack>

                {hasFilters && (
                    <Button
                        variant="contained"
                        onClick={onResetFilters}
                    >
                        پاک کردن فیلترها
                    </Button>
                )}
            </Stack>
        </Paper>
    );
};