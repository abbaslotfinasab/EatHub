// presentation/components/order/OrdersFilterPopover.tsx

import {
    Button,
    Divider,
    FormControl,
    InputLabel,
    MenuItem,
    Popover,
    Select,
    Stack,
    TextField,
    Typography,
} from "@mui/material";


import {
    OrderStatus,
    type OrderStatusType,
    PaymentMethod,
    type PaymentMethodType,
    PaymentStatus,
    type PaymentStatusType,
} from "../../../domain/entities/product/order/Order";
import {orderStatusLabels} from "../../utils/orderStatusLabels.ts";


export type OrderType =
    | "dine_in"
    | "takeaway"
    | "delivery";


export type OrderOrdering =
    | "-created_at"
    | "created_at"
    | "-total_amount"
    | "total_amount";


interface OrdersFilterPopoverProps {


    anchorEl:
        HTMLElement | null;


    open:
        boolean;


    status:
        OrderStatusType | "ALL";


    orderType:
        OrderType | "ALL";


    paymentStatus:
        PaymentStatusType | "ALL";


    paymentMethod:
        PaymentMethodType | "ALL";


    ordering:
        OrderOrdering;


    fromDate:
        string;


    toDate:
        string;


    onClose:
        () => void;


    onStatusChange:
        (
            value: OrderStatusType | "ALL"
        ) => void;


    onOrderTypeChange:
        (
            value: OrderType | "ALL"
        ) => void;


    onPaymentStatusChange:
        (
            value: PaymentStatusType | "ALL"
        ) => void;


    onPaymentMethodChange:
        (
            value: PaymentMethodType | "ALL"
        ) => void;


    onOrderingChange:
        (
            value: OrderOrdering
        ) => void;


    onFromDateChange:
        (
            value: string
        ) => void;


    onToDateChange:
        (
            value: string
        ) => void;


    onClear:
        () => void;

}


export function OrdersFilterPopover({

                                        anchorEl,

                                        open,

                                        status,

                                        orderType,

                                        paymentStatus,

                                        paymentMethod,

                                        ordering,

                                        fromDate,

                                        toDate,


                                        onClose,

                                        onStatusChange,

                                        onOrderTypeChange,

                                        onPaymentStatusChange,

                                        onPaymentMethodChange,

                                        onOrderingChange,

                                        onFromDateChange,

                                        onToDateChange,

                                        onClear,


                                    }: OrdersFilterPopoverProps) {


    return (


        <Popover


            open={open}


            anchorEl={anchorEl}


            onClose={onClose}


            anchorOrigin={{

                vertical:
                    "bottom",

                horizontal:
                    "right",

            }}


            transformOrigin={{

                vertical:
                    "top",

                horizontal:
                    "right",

            }}


            slotProps={{

                paper: {

                    sx: {

                        width: 380,

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
                    فیلتر سفارشات
                </Typography>


                <Divider/>


                <FormControl fullWidth>

                    <InputLabel>
                        وضعیت سفارش
                    </InputLabel>


                    <Select

                        value={status}

                        label="وضعیت سفارش"

                        onChange={(e) => {

                            onStatusChange(
                                e.target.value as OrderStatusType | "ALL"
                            );

                        }}

                    >

                        <MenuItem value="ALL">
                            همه سفارش‌ها
                        </MenuItem>


                        {
                            Object.values(OrderStatus).map(
                                (value) => (

                                    <MenuItem
                                        key={value}
                                        value={value}
                                    >
                                        {
                                            orderStatusLabels[
                                                value as OrderStatusType
                                                ]
                                        }
                                    </MenuItem>

                                )
                            )
                        }


                    </Select>

                </FormControl>


                <FormControl fullWidth>


                    <InputLabel>
                        نوع سفارش
                    </InputLabel>


                    <Select

                        value={orderType}

                        label="نوع سفارش"


                        onChange={(e) =>

                            onOrderTypeChange(
                                e.target.value as OrderType | "ALL"
                            )

                        }

                    >


                        <MenuItem value="ALL">
                            همه
                        </MenuItem>


                        <MenuItem value="dine_in">
                            داخل سالن
                        </MenuItem>


                        <MenuItem value="takeaway">
                            بیرون‌بر
                        </MenuItem>


                        <MenuItem value="delivery">
                            ارسال
                        </MenuItem>


                    </Select>


                </FormControl>


                <FormControl fullWidth>


                    <InputLabel>
                        وضعیت پرداخت
                    </InputLabel>


                    <Select


                        value={paymentStatus}


                        label="وضعیت پرداخت"


                        onChange={(e) => {

                            onPaymentStatusChange(
                                e.target.value as PaymentStatusType | "ALL"
                            );

                        }}


                    >


                        <MenuItem value="ALL">
                            همه
                        </MenuItem>


                        <MenuItem value={PaymentStatus.PENDING}>
                            در انتظار
                        </MenuItem>


                        <MenuItem value={PaymentStatus.PAID}>
                            پرداخت شده
                        </MenuItem>


                        <MenuItem value={PaymentStatus.FAILED}>
                            ناموفق
                        </MenuItem>


                        <MenuItem value={PaymentStatus.REFUNDED}>
                            بازگشت وجه
                        </MenuItem>


                    </Select>


                </FormControl>


                <FormControl fullWidth>


                    <InputLabel>
                        روش پرداخت
                    </InputLabel>


                    <Select


                        value={paymentMethod}


                        label="روش پرداخت"


                        onChange={(e) => {

                            onPaymentMethodChange(
                                e.target.value as PaymentMethodType | "ALL"
                            );

                        }}


                    >


                        <MenuItem value="ALL">
                            همه
                        </MenuItem>


                        <MenuItem value={PaymentMethod.CASH}>
                            نقدی
                        </MenuItem>


                        <MenuItem value={PaymentMethod.CARD}>
                            کارت
                        </MenuItem>


                        <MenuItem value={PaymentMethod.CUSTOMER_ACCOUNT}>
                            حساب مشتری
                        </MenuItem>


                    </Select>


                </FormControl>


                <FormControl fullWidth>


                    <InputLabel>
                        مرتب سازی
                    </InputLabel>


                    <Select


                        value={ordering}


                        label="مرتب سازی"


                        onChange={(e) => {

                            onOrderingChange(
                                e.target.value as OrderOrdering
                            );

                        }}


                    >


                        <MenuItem value="-created_at">

                            جدیدترین

                        </MenuItem>


                        <MenuItem value="created_at">

                            قدیمی‌ترین

                        </MenuItem>


                        <MenuItem value="-total_amount">

                            بیشترین مبلغ

                        </MenuItem>


                        <MenuItem value="total_amount">

                            کمترین مبلغ

                        </MenuItem>


                    </Select>


                </FormControl>


                <Stack
                    direction="row"
                    spacing={2}
                >


                    <TextField

                        fullWidth

                        label="از تاریخ"

                        type="date"

                        value={fromDate}


                        onChange={(e) =>

                            onFromDateChange(
                                e.target.value
                            )

                        }


                        slotProps={{

                            inputLabel: {

                                shrink: true,

                            },

                        }}

                    />


                    <TextField

                        fullWidth

                        label="تا تاریخ"

                        type="date"

                        value={toDate}


                        onChange={(e) =>

                            onToDateChange(
                                e.target.value
                            )

                        }


                        slotProps={{

                            inputLabel: {

                                shrink: true,

                            },

                        }}

                    />


                </Stack>


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