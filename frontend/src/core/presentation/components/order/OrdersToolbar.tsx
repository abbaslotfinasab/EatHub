// presentation/components/order/OrdersToolbar.tsx

import {useMemo, useState, } from "react";

import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import FilterListRoundedIcon from "@mui/icons-material/FilterListRounded";

import {
    Badge,
    Button,
    InputAdornment,
    Paper,
    Stack,
    TextField,
} from "@mui/material";

import {
    type OrderStatusType, type PaymentMethodType, type PaymentStatusType,
} from "../../../domain/entities/product/order/Order";

import {type OrderOrdering, OrdersFilterPopover, type OrderType} from "./OrdersFilterPopover";

interface OrdersToolbarProps {
    search: string;

    status: OrderStatusType | "ALL";

    onSearchChange: (
        value: string,
    ) => void;

    onStatusChange: (
        status: OrderStatusType | "ALL",
    ) => void;
}

export const OrdersToolbar = ({
                                  search,
                                  onSearchChange,
                              }: OrdersToolbarProps) => {

    // ===========================
    // State
    // ===========================

    const [anchorEl, setAnchorEl] =
        useState<HTMLElement | null>(null);

    const [status, setStatus] =
        useState<OrderStatusType | "ALL">("ALL");

    const [orderType, setOrderType] =
        useState<OrderType | "ALL">("ALL");

    const [paymentStatus, setPaymentStatus] =
        useState<PaymentStatusType | "ALL">("ALL");

    const [paymentMethod, setPaymentMethod] =
        useState<PaymentMethodType | "ALL">("ALL");

    const [ordering, setOrdering] =
        useState<OrderOrdering>("-created_at");

    const [fromDate, setFromDate] =
        useState("");

    const [toDate, setToDate] =
        useState("");

    // ===========================
    // Derived State
    // ===========================

    const filtersActive = useMemo(
        () => status !== "ALL",
        [status],
    );

    // ===========================
    // Handlers
    // ===========================

    const handleOpenFilters = (
        event: React.MouseEvent<HTMLElement>,
    ) => {
        setAnchorEl(
            event.currentTarget,
        );
    };

    const handleCloseFilters = () => {
        setAnchorEl(null);
    };

    // ===========================
    // Render
    // ===========================

    return (
        <>
            <Paper
                elevation={0}
                sx={{
                    p: 2,
                    borderRadius: 1,
                    border: "1px solid",
                    borderColor: "divider",
                    bgcolor: "background.paper",
                }}
            >
                <Stack
                    sx={{
                        flexDirection: {
                            xs: "column",
                            md: "row",
                        },
                        gap: 2,
                        alignItems: "center",
                    }}
                >
                    <TextField
                        fullWidth
                        value={search}
                        placeholder="جستجوی مشتری، شماره سفارش..."
                        onChange={(e) =>
                            onSearchChange(
                                e.target.value,
                            )
                        }
                        sx={{
                            "& .MuiOutlinedInput-root": {
                                height: 56,
                                borderRadius: 1,

                                "& fieldset": {
                                    borderColor: "#E2E8F0",
                                },

                                "&:hover fieldset": {
                                    borderColor: "#1F4A33",
                                },

                                "&.Mui-focused fieldset": {
                                    borderColor: "#10281A",
                                    borderWidth: 2,
                                },
                            },
                        }}
                        slotProps={{
                            input: {
                                startAdornment: (
                                    <InputAdornment position="start">
                                        <SearchRoundedIcon/>
                                    </InputAdornment>
                                ),
                            },
                        }}
                    />

                    <Badge
                        color="primary"
                        variant="dot"
                        invisible={!filtersActive}
                    >
                        <Button
                            variant="outlined"
                            startIcon={
                                <FilterListRoundedIcon/>
                            }
                            onClick={
                                handleOpenFilters
                            }
                            sx={{
                                width: {
                                    xs: "100%",
                                    md: 150,
                                },

                                height: 56,

                                borderRadius: 1,

                                flexShrink: 0,
                            }}
                        >
                            فیلترها
                        </Button>
                    </Badge>
                </Stack>
            </Paper>

            <OrdersFilterPopover
                open={Boolean(anchorEl)}
                anchorEl={anchorEl}

                status={status}
                orderType={orderType}
                paymentStatus={paymentStatus}
                paymentMethod={paymentMethod}
                ordering={ordering}
                fromDate={fromDate}
                toDate={toDate}

                onStatusChange={setStatus}
                onOrderTypeChange={setOrderType}
                onPaymentStatusChange={setPaymentStatus}
                onPaymentMethodChange={setPaymentMethod}
                onOrderingChange={setOrdering}
                onFromDateChange={setFromDate}
                onToDateChange={setToDate}

                onClear={() => {
                    setStatus("ALL");
                    setOrderType("ALL");
                    setPaymentStatus("ALL");
                    setPaymentMethod("ALL");
                    setOrdering("-created_at");
                    setFromDate("");
                    setToDate("");
                }}

                onClose={handleCloseFilters}
            />
        </>
    );
};