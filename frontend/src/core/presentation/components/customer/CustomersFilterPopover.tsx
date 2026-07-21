import {
    Button,
    Divider,
    FormControl,
    InputLabel,
    MenuItem,
    Popover,
    Select,
    Stack,
    Typography,
} from "@mui/material";

import type {
    CustomerBalanceFilter,
    CustomerOrdering,
    CustomerOrdersFilter,
} from "../../../domain/objects/filters/CustomerSearchFilters";

interface CustomersFilterPopoverProps {
    anchorEl: HTMLElement | null;

    open: boolean;

    balance: CustomerBalanceFilter;

    orders: CustomerOrdersFilter;

    ordering: CustomerOrdering;

    onClose(): void;

    onBalanceChange(
        value: CustomerBalanceFilter,
    ): void;

    onOrdersChange(
        value: CustomerOrdersFilter,
    ): void;

    onOrderingChange(
        value: CustomerOrdering,
    ): void;

    onClear(): void;
}

export function CustomersFilterPopover({
    anchorEl,
    open,
    balance,
    orders,
    ordering,
    onClose,
    onBalanceChange,
    onOrdersChange,
    onOrderingChange,
    onClear,
}: CustomersFilterPopoverProps) {

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
                        width: 360,
                        maxWidth: "calc(100vw - 32px)",
                        p: 3,
                        mt: 1,
                        borderRadius: 4,
                    },
                },
            }}
        >
            <Stack
                sx={{
                    gap: 3,
                }}
            >
                <Typography
                    variant="h6"
                    sx={{
                        fontWeight: 700,
                    }}
                >
                    فیلتر مشتریان
                </Typography>

                <Divider />

                <FormControl fullWidth>
                    <InputLabel>
                        وضعیت حساب
                    </InputLabel>

                    <Select
                        label="وضعیت حساب"
                        value={balance}
                        onChange={(e) =>
                            onBalanceChange(
                                e.target.value as CustomerBalanceFilter,
                            )
                        }
                    >
                        <MenuItem value="ALL">
                            همه مشتریان
                        </MenuItem>

                        <MenuItem value="CREDITOR">
                            بستانکار
                        </MenuItem>

                        <MenuItem value="DEBTOR">
                            بدهکار
                        </MenuItem>

                        <MenuItem value="ZERO">
                            بدون مانده
                        </MenuItem>
                    </Select>
                </FormControl>

                <FormControl fullWidth>
                    <InputLabel>
                        تعداد سفارش
                    </InputLabel>

                    <Select
                        label="تعداد سفارش"
                        value={orders}
                        onChange={(e) =>
                            onOrdersChange(
                                e.target.value as CustomerOrdersFilter,
                            )
                        }
                    >
                        <MenuItem value="ALL">
                            همه
                        </MenuItem>

                        <MenuItem value="5">
                            بیش از ۵ سفارش
                        </MenuItem>

                        <MenuItem value="10">
                            بیش از ۱۰ سفارش
                        </MenuItem>

                        <MenuItem value="50">
                            بیش از ۵۰ سفارش
                        </MenuItem>
                    </Select>
                </FormControl>

                <FormControl fullWidth>
                    <InputLabel>
                        مرتب‌سازی
                    </InputLabel>

                    <Select
                        label="مرتب‌سازی"
                        value={ordering}
                        onChange={(e) =>
                            onOrderingChange(
                                e.target.value as CustomerOrdering,
                            )
                        }
                    >
                        <MenuItem value="-created_at">
                            جدیدترین
                        </MenuItem>

                        <MenuItem value="created_at">
                            قدیمی‌ترین
                        </MenuItem>

                        <MenuItem value="-total_spent">
                            بیشترین خرید
                        </MenuItem>

                        <MenuItem value="-total_orders">
                            بیشترین سفارش
                        </MenuItem>

                        <MenuItem value="name">
                            نام مشتری (الفبا)
                        </MenuItem>
                    </Select>
                </FormControl>

                <Divider />

                <Stack
                    sx={{
                        flexDirection: "row",
                        gap: 1,
                    }}
                >
                    <Button
                        fullWidth
                        variant="outlined"
                        color="inherit"
                        onClick={onClear}
                    >
                        حذف فیلترها
                    </Button>

                    <Button
                        fullWidth
                        variant="contained"
                        onClick={onClose}
                    >
                        بستن
                    </Button>
                </Stack>
            </Stack>
        </Popover>
    );
}