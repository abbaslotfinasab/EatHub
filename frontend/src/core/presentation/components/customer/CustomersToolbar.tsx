import {useMemo, useState} from "react";

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

import {CustomersFilterPopover} from "./CustomersFilterPopover";

import type {
    CustomerSearchFilters,
} from "../../../domain/objects/filters/CustomerSearchFilters";


export interface CustomersToolbarProps {

    search: string;

    filters: CustomerSearchFilters;

    onSearchChange: (
        value: string
    ) => void;

    onFiltersChange: (
        filters: CustomerSearchFilters
    ) => void;

}


export function CustomersToolbar({

    search,

    filters,

    onSearchChange,

    onFiltersChange,

}: CustomersToolbarProps) {


    const [
        anchorEl,
        setAnchorEl,
    ] = useState<HTMLElement | null>(null);


    const filtersActive =
        useMemo(
            () => {

                return Boolean(

                    filters.balance ||
                    filters.minOrders||
                    (
                        filters.ordering &&
                        filters.ordering !== "-created_at"
                    ) ||
                    filters.createdAfter ||
                    filters.createdBefore

                );

            },
            [
                filters,
            ],
        );


    const clearFilters = () => {

        onFiltersChange({

            ordering: "-created_at",

        });

    };


    return (

        <>

            <Paper
                elevation={0}
                sx={{
                    p: 2,

                    borderRadius: 1,

                    border: "1px solid",

                    borderColor: "divider",
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

                        placeholder="جستجوی نام یا شماره موبایل..."

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
                                    borderColor:
                                        "#E2E8F0",
                                },

                                "&:hover fieldset": {
                                    borderColor:
                                        "#1F4A33",
                                },

                                "&.Mui-focused fieldset": {

                                    borderColor:
                                        "#10281A",

                                    borderWidth:
                                        2,
                                },

                            },
                        }}

                        slotProps={{
                            input: {

                                startAdornment: (

                                    <InputAdornment
                                        position="start"
                                    >
                                        <SearchRoundedIcon/>

                                    </InputAdornment>

                                ),
                            },
                        }}

                    />


                    <Badge

                        variant="dot"

                        color="primary"

                        invisible={
                            !filtersActive
                        }

                    >

                        <Button

                            variant="outlined"

                            endIcon={
                                <FilterListRoundedIcon/>
                            }

                            onClick={(e) => {

                                setAnchorEl(
                                    e.currentTarget,
                                );

                            }}

                            sx={{

                                width: {

                                    xs: "100%",

                                    md: 150,

                                },

                                height: 56,

                                borderRadius: 1,

                                flexShrink: 0,

                                "& .MuiButton-endIcon": {

                                    marginRight: 8,

                                    marginLeft: 0,

                                },

                            }}

                        >
                            فیلترها

                        </Button>

                    </Badge>


                </Stack>


            </Paper>


            <CustomersFilterPopover

                open={
                    Boolean(anchorEl)
                }


                anchorEl={
                    anchorEl
                }


                balance={
                    filters.balance ?? "ALL"
                }


                minOrders={
                    filters.minOrders ?? "ALL"
                }


                ordering={
                    filters.ordering ?? "-created_at"
                }


                onBalanceChange={(value) => {

                    onFiltersChange({

                        ...filters,

                        balance:
                            value === "ALL"
                                ? undefined
                                : value,

                    });

                }}


                onMinOrdersChange={(value) => {

                    onFiltersChange({

                        ...filters,

                        minOrders:
                            value === "ALL"
                                ? undefined
                                : value,

                    });

                }}


                onOrderingChange={(value) => {

                    onFiltersChange({

                        ...filters,

                        ordering:
                            value,

                    });

                }}


                onClear={
                    clearFilters
                }


                onClose={() => {

                    setAnchorEl(null);

                }}

            />

        </>

    );

}