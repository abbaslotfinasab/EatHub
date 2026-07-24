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
    CustomerMinOrdersFilter,
    CustomerOrdering,
} from "../../../domain/objects/filters/CustomerSearchFilters";


interface CustomersFilterPopoverProps {

    anchorEl: HTMLElement | null;

    open: boolean;


    balance: CustomerBalanceFilter;

    minOrders: CustomerMinOrdersFilter;

    ordering: CustomerOrdering;


    onClose: () => void;


    onBalanceChange: (
        value: CustomerBalanceFilter
    ) => void;


    onMinOrdersChange: (
        value: CustomerMinOrdersFilter
    ) => void;


    onOrderingChange: (
        value: CustomerOrdering
    ) => void;


    onClear: () => void;

}


export function CustomersFilterPopover({

                                           anchorEl,

                                           open,

                                           balance,

                                           minOrders,

                                           ordering,

                                           onClose,

                                           onBalanceChange,

                                           onMinOrdersChange,

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

                        maxWidth:
                            "calc(100vw - 32px)",

                        p: 3,

                        mt: 1,

                        borderRadius: 3,

                    },

                },

            }}

        >

            <Stack spacing={3}>


                <Typography
                    variant="h6"
                    sx={{
                        fontWeight: 700,
                    }}
                >
                    فیلتر مشتریان
                </Typography>


                <Divider/>


                <FormControl fullWidth>

                    <InputLabel>
                        وضعیت حساب
                    </InputLabel>


                    <Select

                        value={balance}

                        label="وضعیت حساب"

                        onChange={(event) => {

                            const value =
                                event.target.value as CustomerBalanceFilter;

                            onBalanceChange(value);

                        }}

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

                        value={minOrders}

                        label="تعداد سفارش"

                        onChange={(event) => {

                            const value =
                                event.target.value as CustomerMinOrdersFilter;

                            onMinOrdersChange(value);

                        }}

                    >

                        <MenuItem value="ALL">
                            همه
                        </MenuItem>


                        <MenuItem value="5">
                            بیشتر از ۵ سفارش
                        </MenuItem>


                        <MenuItem value="10">
                            بیشتر از ۱۰ سفارش
                        </MenuItem>


                        <MenuItem value="50">
                            بیشتر از ۵۰ سفارش
                        </MenuItem>


                    </Select>


                </FormControl>


                <FormControl fullWidth>

                    <InputLabel>
                        مرتب‌سازی
                    </InputLabel>


                    <Select

                        value={ordering}

                        label="مرتب‌سازی"

                        onChange={(event) => {

                            const value =
                                event.target.value as CustomerOrdering;

                            onOrderingChange(value);

                        }}

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
                            نام مشتری
                        </MenuItem>


                    </Select>


                </FormControl>


                <Divider/>


                <Stack
                    direction="row"
                    spacing={1}
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
                        اعمال
                    </Button>


                </Stack>


            </Stack>


        </Popover>

    );

}