// presentation/components/order/OrdersFilterPopover.tsx

import {
    Box,
    Button,
    Divider,
    FormControlLabel,
    Popover,
    Radio,
    RadioGroup,
    Stack,
    Typography,
} from "@mui/material";

import {
    OrderStatus,
    type OrderStatusType,
} from "../../../domain/entities/product/order/Order";

interface OrdersFilterPopoverProps {
    anchorEl: HTMLElement | null;
    open: boolean;
    status: OrderStatusType | "ALL";

    onClose: () => void;

    onStatusChange: (
        status: OrderStatusType | "ALL",
    ) => void;

    onClear: () => void;
}

const STATUS_OPTIONS = [
    {
        label: "همه",
        value: "ALL",
    },
    {
        label: "در انتظار",
        value: OrderStatus.PENDING,
    },
    {
        label: "تأیید شده",
        value: OrderStatus.CONFIRMED,
    },
    {
        label: "در حال آماده‌سازی",
        value: OrderStatus.PREPARING,
    },
    {
        label: "آماده تحویل",
        value: OrderStatus.READY,
    },
    {
        label: "تحویل شده",
        value: OrderStatus.COMPLETED,
    },
    {
        label: "لغو شده",
        value: OrderStatus.CANCELLED,
    },
] satisfies {
    label: string;
    value: OrderStatusType | "ALL";
}[];

export const OrdersFilterPopover = ({
    anchorEl,
    open,
    status,
    onClose,
    onStatusChange,
    onClear,
}: OrdersFilterPopoverProps) => {
    return (
        <Popover
            open={open}
            anchorEl={anchorEl}
            onClose={onClose}
            anchorOrigin={{
                vertical: "bottom",
                horizontal: "right",
            }}
            transformOrigin={{
                vertical: "top",
                horizontal: "right",
            }}
            slotProps={{
                paper: {
                    sx: {
                        width: 320,
                        borderRadius: 4,
                        mt: 1,
                        p: 2,
                    },
                },
            }}
        >
            <Stack spacing={2}>
                <Typography
                    sx={{
                        fontWeight: 700,
                        fontSize: 16,
                    }}
                >
                    فیلتر سفارشات
                </Typography>

                <Divider />

                {/* وضعیت سفارش */}

                <Box>
                    <Typography
                        sx={{
                            mb: 1.5,
                            fontWeight: 600,
                            color: "text.secondary",
                            fontSize: 14,
                        }}
                    >
                        وضعیت سفارش
                    </Typography>

                    <RadioGroup
                        value={status}
                        onChange={(e) =>
                            onStatusChange(
                                e.target.value as
                                    | OrderStatusType
                                    | "ALL",
                            )
                        }
                    >
                        {STATUS_OPTIONS.map((item) => (
                            <FormControlLabel
                                key={item.value}
                                value={item.value}
                                control={<Radio />}
                                label={item.label}
                            />
                        ))}
                    </RadioGroup>
                </Box>

                <Divider />

                <Stack
                    sx={{
                        flexDirection: "row",
                        justifyContent: "space-between",
                        gap: 1,
                    }}
                >
                    <Button
                        variant="outlined"
                        color="inherit"
                        fullWidth
                        onClick={onClear}
                    >
                        حذف فیلترها
                    </Button>

                    <Button
                        variant="contained"
                        fullWidth
                        onClick={onClose}
                    >
                        اعمال
                    </Button>
                </Stack>
            </Stack>
        </Popover>
    );
};