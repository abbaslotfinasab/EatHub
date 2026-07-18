import { useMemo } from "react";

import ReceiptLongRoundedIcon from "@mui/icons-material/ReceiptLongRounded";

import {
    Button,
    Divider,
    Paper,
    Stack,
    Typography,
} from "@mui/material";
import { useGetMenus } from "../../hooks/menu/useGetMenus.ts";
import { useOrderItems } from "../../forms/order/useOrderItems.ts";
import {formatCurrency} from "../../utils/formatCurrency.ts";



export const OrderSummaryCard = () => {

    const {
        data: menus = [],
    } = useGetMenus();

    const {
        orderItems,
    } = useOrderItems();

    // =========================
    // Flatten Menu Items
    // =========================

    const menuItems = useMemo(() => {

        return menus.flatMap(
            menu => menu.items,
        );

    }, [menus]);

    // =========================
    // Calculations
    // =========================

    const summary = useMemo(() => {

        const subtotal =
            orderItems.reduce((sum, item) => {

                const menuItem =
                    menuItems.find(
                        x => x.id === item.menuItemId,
                    );

                if (!menuItem) {
                    return sum;
                }

                return (
                    sum +
                    menuItem.price *
                    item.quantity
                );

            }, 0);

        const totalItems =
            orderItems.reduce(
                (sum, item) =>
                    sum + item.quantity,
                0,
            );

        const discount = 0;

        const tax = 0;

        const total =
            subtotal -
            discount +
            tax;

        return {
            subtotal,
            totalItems,
            discount,
            tax,
            total,
        };

    }, [
        orderItems,
        menuItems,
    ]);

    return (

        <Paper
            variant="outlined"
            sx={{
                p: 3,
                borderRadius: 3,
            }}
        >

            <Stack spacing={2}>

                <Stack
                    sx={{
                        flexDirection: "row",
                        alignItems: "center",
                        gap: 1,
                    }}
                >

                    <ReceiptLongRoundedIcon
                        color="primary"
                    />

                    <Typography
                        variant="h6"
                        sx={{
                            fontWeight: 700,
                        }}
                    >
                        خلاصه سفارش
                    </Typography>

                </Stack>

                <Divider />

                {/* تعداد */}

                <Stack
                    sx={{
                        flexDirection: "row",
                        justifyContent: "space-between",
                    }}
                >

                    <Typography
                        color="text.secondary"
                    >
                        تعداد آیتم‌ها
                    </Typography>

                    <Typography
                        sx={{
                            fontWeight: 700,
                        }}
                    >
                        {summary.totalItems}
                    </Typography>

                </Stack>

                {/* جمع */}

                <Stack
                    sx={{
                        flexDirection: "row",
                        justifyContent: "space-between",
                    }}
                >

                    <Typography
                        color="text.secondary"
                    >
                        جمع جزء
                    </Typography>

                    <Typography
                        sx={{
                            fontWeight: 700,
                        }}
                    >
                        {formatCurrency(
                            summary.subtotal,
                        )}
                    </Typography>

                </Stack>

                {/* تخفیف */}

                <Stack
                    sx={{
                        flexDirection: "row",
                        justifyContent: "space-between",
                    }}
                >

                    <Typography
                        color="text.secondary"
                    >
                        تخفیف
                    </Typography>

                    <Typography
                        sx={{
                            fontWeight: 700,
                        }}
                    >
                        {formatCurrency(
                            summary.discount,
                        )}
                    </Typography>

                </Stack>

                {/* مالیات */}

                <Stack
                    sx={{
                        flexDirection: "row",
                        justifyContent: "space-between",
                    }}
                >

                    <Typography
                        color="text.secondary"
                    >
                        مالیات
                    </Typography>

                    <Typography
                        sx={{
                            fontWeight: 700,
                        }}
                    >
                        {formatCurrency(
                            summary.tax,
                        )}
                    </Typography>

                </Stack>

                <Divider />

                {/* مبلغ نهایی */}

                <Stack
                    sx={{
                        flexDirection: "row",
                        justifyContent: "space-between",
                        alignItems: "center",
                    }}
                >

                    <Typography
                        variant="h6"
                        sx={{
                            fontWeight: 700,
                        }}
                    >
                        مبلغ نهایی
                    </Typography>

                    <Typography
                        variant="h5"
                        color="primary"
                        sx={{
                            fontWeight: 800,
                        }}
                    >
                        {formatCurrency(
                            summary.total,
                        )}
                    </Typography>

                </Stack>

                <Button
                    fullWidth
                    size="large"
                    variant="contained"
                    sx={{
                        mt: 1,
                        height: 54,
                        borderRadius: 3,
                    }}
                >
                    ثبت سفارش
                </Button>

            </Stack>

        </Paper>

    );

};