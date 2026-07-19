// presentation/components/order/OrdersToolbar.tsx

import { useState } from "react";

import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import FilterListRoundedIcon from "@mui/icons-material/FilterListRounded";
import RefreshRoundedIcon from "@mui/icons-material/RefreshRounded";

import {
    Button,
    IconButton,
    InputAdornment,
    Stack,
    TextField,
    Tooltip,
} from "@mui/material";

import {
    type OrderStatusType,
} from "../../../domain/entities/product/order/Order";

import { OrdersFilterPopover } from "./OrdersFilterPopover";

interface OrdersToolbarProps {
    search: string;

    status: OrderStatusType | "ALL";

    onSearchChange: (value: string) => void;

    onStatusChange: (
        status: OrderStatusType | "ALL",
    ) => void;

    onRefresh?: () => void;
}

export const OrdersToolbar = ({
    search,
    status,
    onSearchChange,
    onStatusChange,
    onRefresh,
}: OrdersToolbarProps) => {

    // ===========================
    // State
    // ===========================

    const [anchorEl, setAnchorEl] =
        useState<HTMLElement | null>(null);

    // ===========================
    // Handlers
    // ===========================

    const handleOpenFilters = (
        event: React.MouseEvent<HTMLElement>,
    ) => {
        setAnchorEl(event.currentTarget);
    };

    const handleCloseFilters = () => {
        setAnchorEl(null);
    };

    // ===========================
    // Render
    // ===========================

    return (
        <>
            <Stack
                sx={{
                    flexDirection: {
                        xs: "column",
                        md: "row",
                    },

                    alignItems: "center",

                    gap: 2,
                }}
            >

                <TextField
                    fullWidth
                    placeholder="جستجوی مشتری، شماره سفارش..."
                    value={search}
                    onChange={(e) =>
                        onSearchChange(
                            e.target.value,
                        )
                    }
                    sx={{
                       "& .MuiOutlinedInput-root": {
                        height: 58,
                        borderRadius: 4,
                        bgcolor: "#fff",

                        "& fieldset": {
                            borderColor: "#E2E8F0",
                        },

                        "&:hover fieldset": {
                            borderColor: "#1F4A33",
                        },

                        "&.Mui-focused fieldset": {
                            borderColor: "#10281A",
                            borderWidth: "2px",
                        },
                    },
                    }}
                    slotProps={{
                        input: {
                            startAdornment: (
                                <InputAdornment position="start">
                                    <SearchRoundedIcon />
                                </InputAdornment>
                            ),
                        },
                    }}
                />

                <Button
                    variant="outlined"
                    startIcon={
                        <FilterListRoundedIcon />
                    }
                    onClick={
                        handleOpenFilters
                    }
                    sx={{
                        minWidth: 150,
                        height: 56,
                        borderRadius: 3,
                        flexShrink: 0,
                    }}
                >
                    فیلترها
                </Button>

                <Tooltip title="بروزرسانی">
                    <IconButton
                        onClick={onRefresh}
                        sx={{
                            width: 56,
                            height: 56,
                            border: "1px solid",
                            borderColor:
                                "divider",
                            borderRadius: 3,
                            flexShrink: 0,
                        }}
                    >
                        <RefreshRoundedIcon />
                    </IconButton>
                </Tooltip>

            </Stack>

            <OrdersFilterPopover
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                status={status}
                onClose={
                    handleCloseFilters
                }
                onStatusChange={
                    onStatusChange
                }
                onClear={() =>
                    onStatusChange("ALL")
                }
            />
        </>
    );
};